"""Prepare and serve the existing cross-team RAG on this machine; no alternate pipeline."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG = ROOT / 'team1_data/retrieval/retrieval_v2.json'
DEFAULT_CHUNKS = ROOT / 'data/doanh-nghiep/processed/chunks.jsonl'
DEFAULT_CACHE = ROOT / '.local/team3/live-rag/huggingface'


class BuildProgress:
    """Observe batched calls to Team1's embedder without replacing its encoding."""
    def __init__(self, embedder, batch_size):
        self.embedder, self.batch_size = embedder, batch_size

    def __getattr__(self, name):
        return getattr(self.embedder, name)

    def embed_passages(self, texts):
        import numpy as np
        vectors = []
        for start in range(0, len(texts), self.batch_size):
            vectors.append(self.embedder.embed_passages(texts[start:start + self.batch_size]))
            done = min(start + self.batch_size, len(texts))
            if start == 0 or done % 128 == 0 or done == len(texts):
                print(json.dumps({'event': 'embedding_progress', 'completed': done, 'total': len(texts)}), flush=True)
        return np.concatenate(vectors, axis=0)


def digest(path):
    result = hashlib.sha256()
    with Path(path).open('rb') as source:
        for block in iter(lambda: source.read(1024 * 1024), b''):
            result.update(block)
    return result.hexdigest()


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def configuration(path):
    value = read(path)
    # Team2's factory currently constructs this Hybrid configuration. Reject a
    # different selection rather than silently advertising settings not applied.
    if (value['method'] != 'hybrid_rrf' or value['hybrid']['weights'] != [.5, 1.0]
            or value['hybrid']['rrf_k'] != 60 or value['hybrid']['candidate_limit'] != 100
            or value['bm25']['method'] != 'lucene' or value['dense']['distance'] != 'cosine'
            or type(value['top_k']) is not int or not 1 <= value['top_k'] <= 50
            or not value['dense']['embedding_revision']):
        raise ValueError('Selected configuration is not supported by the existing runtime')
    return value


def configure_cache(path, allow_download=False):
    path = Path(path).resolve()
    os.environ['HF_HOME'] = str(path)
    # Explicit hub location also takes precedence over inherited machine settings.
    os.environ['HF_HUB_CACHE'] = str(path / 'hub')
    os.environ['HF_HUB_OFFLINE'] = '0' if allow_download else '1'
    os.environ['TRANSFORMERS_OFFLINE'] = '0' if allow_download else '1'
    os.environ['HF_HUB_DISABLE_PROGRESS_BARS'] = '1'


def prepare(output, config_path, chunks, cache, allow_download=False, batch_size=1):
    config_path, chunks, output = map(lambda p: Path(p).resolve(), (config_path, chunks, output))
    selected = configuration(config_path)
    source_hash = digest(chunks)
    if output.exists():
        raise ValueError('Output already exists; use a fresh directory or serve the existing runtime')
    configure_cache(cache, allow_download)
    from qdrant_client import QdrantClient
    from team1_data.retrieval import BM25Retriever, DenseRetriever, SentenceTransformerEmbedder
    from team2_rag.reranker import BGEScorer

    output.mkdir(parents=True)
    version = selected['version'] + '-' + source_hash[:12]
    dense_config = selected['dense']
    sparse = BM25Retriever.from_jsonl(chunks, k1=selected['bm25']['k1'], b=selected['bm25']['b'],
                                      legal_status=selected['legal_status'])
    sparse.save(output / 'bm25', index_version=version)
    print(json.dumps({'event': 'bm25_ready', 'chunks': len(sparse.chunk_ids)}), flush=True)
    embedder = SentenceTransformerEmbedder(
        name=dense_config['embedding_model'], revision=dense_config['embedding_revision'],
        query_prefix=dense_config['query_prefix'], passage_prefix=dense_config['passage_prefix'],
        device='cpu', batch_size=batch_size)
    client = QdrantClient(path=str(output / 'qdrant'))
    try:
        dense = DenseRetriever.from_jsonl(chunks, embedder=BuildProgress(embedder, batch_size), client=client,
                                         index_version=version, legal_status=selected['legal_status'])
        if set(sparse.chunk_ids) != set(dense.chunk_ids):
            raise ValueError('BM25 and Dense contain different chunk IDs')
        dense.save(output / 'dense')
    finally:
        client.close()
    chunk_count = len(dense.chunk_ids)
    print(json.dumps({'event': 'dense_ready', 'chunks': chunk_count}), flush=True)
    # Free the build-time embedding model before warming the reranker on small machines.
    del dense, embedder, sparse
    import gc
    gc.collect()
    # Warm the exact scorer used by Team2, so preparation cannot claim success
    # while only the embedding model is available.
    BGEScorer()([('Doanh nghiep', 'Quy dinh ve doanh nghiep.')])
    manifest = {'configuration': str(config_path), 'configuration_sha256': digest(config_path),
                'chunks': str(chunks), 'chunks_sha256': source_hash, 'model_cache': str(Path(cache).resolve()),
                'index_version': version, 'chunk_count': chunk_count,
                'top_k': selected['top_k'], 'strict_rerank': True}
    (output / 'runtime.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    print(json.dumps({'event': 'runtime_prepared', 'runtime_dir': str(output),
                      'top_k': selected['top_k'], 'chunk_count': manifest['chunk_count']}), flush=True)
    return manifest


def runtime_environment(directory):
    directory = Path(directory).resolve()
    manifest = read(directory / 'runtime.json')
    selected = configuration(manifest['configuration'])
    if (digest(manifest['configuration']) != manifest['configuration_sha256']
            or digest(manifest['chunks']) != manifest['chunks_sha256']
            or selected['top_k'] != manifest['top_k'] or manifest['strict_rerank'] is not True):
        raise ValueError('Runtime corpus/configuration changed; prepare a fresh runtime')
    bm, dense = [read(directory / kind / 'index_manifest.json') for kind in ('bm25', 'dense')]
    if (bm['index_version'] != manifest['index_version'] or dense['index_version'] != manifest['index_version']
            or set(bm['chunk_ids']) != set(dense['chunk_ids'])
            or len(dense['chunk_ids']) != manifest['chunk_count']
            or dense['embedding_model'] != selected['dense']['embedding_model']
            or dense['embedding_revision'] != selected['dense']['embedding_revision']):
        raise ValueError('Runtime index manifests do not match the selected configuration')
    return manifest, {'RAG_BM25_INDEX': str(directory / 'bm25'), 'RAG_DENSE_INDEX': str(directory / 'dense'),
                      'RAG_QDRANT_PATH': str(directory / 'qdrant'), 'RAG_CHUNKS': manifest['chunks'],
                      'RAG_TOP_K': str(manifest['top_k']), 'RAG_STRICT_RERANK': 'true'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    build = commands.add_parser('prepare')
    build.add_argument('--output-dir', type=Path, required=True)
    build.add_argument('--configuration', type=Path, default=DEFAULT_CONFIG)
    build.add_argument('--chunks', type=Path, default=DEFAULT_CHUNKS)
    build.add_argument('--model-cache', type=Path, default=DEFAULT_CACHE)
    build.add_argument('--allow-model-download', action='store_true')
    build.add_argument('--embedding-batch-size', type=int, default=1)
    for name in ('check', 'serve'):
        cmd = commands.add_parser(name)
        cmd.add_argument('--runtime-dir', type=Path, required=True)
        if name == 'serve': cmd.add_argument('--port', type=int, default=8001)
    args = parser.parse_args()
    sys.path.insert(0, str(ROOT))
    os.chdir(ROOT)  # Team2 reads the existing root .env; never copy its secrets.
    try:
        if args.command == 'prepare':
            if args.embedding_batch_size < 1: parser.error('embedding batch size must be positive')
            prepare(args.output_dir, args.configuration, args.chunks, args.model_cache,
                    args.allow_model_download, args.embedding_batch_size)
        else:
            manifest, env = runtime_environment(args.runtime_dir)
            if args.command == 'check':
                print(json.dumps({'status': 'artifacts_valid', 'index_version': manifest['index_version'],
                                  'chunk_count': manifest['chunk_count'], 'top_k': manifest['top_k']}))
            else:
                configure_cache(manifest['model_cache'])
                os.environ.update(env)
                import uvicorn
                uvicorn.run('team2_rag.api:create_app', factory=True, host='127.0.0.1', port=args.port)
    except (OSError, ValueError, KeyError, ImportError) as exc:
        # Do not print provider settings, arbitrary exception bodies or .env data.
        print(json.dumps({'status': 'failed', 'error_type': type(exc).__name__}), file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
