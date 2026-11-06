"""Runtime artifacts must fail closed before model loading or API startup."""
import json
from pathlib import Path
import tempfile
import unittest

from team3_fullstack.tools.local_rag import DEFAULT_CONFIG, digest, prepare, runtime_environment


class LocalRuntimeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.config = self.root / 'config.json'
        self.config.write_text(DEFAULT_CONFIG.read_text(encoding='utf-8'), encoding='utf-8')
        self.chunks = self.root / 'chunks.jsonl'; self.chunks.write_text('corpus-v1')
        self.runtime = self.root / 'runtime'; self.runtime.mkdir()
        self.manifest = {'configuration': str(self.config), 'configuration_sha256': digest(self.config),
                         'chunks': str(self.chunks), 'chunks_sha256': digest(self.chunks),
                         'model_cache': str(self.root / 'cache'), 'index_version': 'test-v1',
                         'chunk_count': 2, 'top_k': 20, 'strict_rerank': True}
        (self.runtime / 'runtime.json').write_text(json.dumps(self.manifest))
        selected = json.loads(self.config.read_text(encoding='utf-8'))
        for kind in ('bm25', 'dense'):
            (self.runtime / kind).mkdir()
            value = {'index_version': 'test-v1', 'chunk_ids': ['c1', 'c2'],
                     'embedding_model': selected['dense']['embedding_model'],
                     'embedding_revision': selected['dense']['embedding_revision']}
            (self.runtime / kind / 'index_manifest.json').write_text(json.dumps(value))

    def test_changed_corpus_or_configuration_rejected(self):
        for path in (self.chunks, self.config):
            with self.subTest(path=path.name):
                original = path.read_text(encoding='utf-8')
                path.write_text(original + ' ', encoding='utf-8')
                with self.assertRaisesRegex(ValueError, 'changed'):
                    runtime_environment(self.runtime)
                path.write_text(original, encoding='utf-8')

    def test_mixed_index_versions_ids_or_models_rejected(self):
        path = self.runtime / 'dense/index_manifest.json'
        original = json.loads(path.read_text())
        for key, value in [('index_version', 'different'), ('chunk_ids', ['c1', 'other']),
                           ('embedding_model', 'different'), ('embedding_revision', 'different')]:
            with self.subTest(field=key):
                path.write_text(json.dumps({**original, key: value}))
                with self.assertRaisesRegex(ValueError, 'index manifests'):
                    runtime_environment(self.runtime)

    def test_selected_settings_forwarded_without_secret_fields(self):
        _, env = runtime_environment(self.runtime)
        self.assertEqual(env['RAG_TOP_K'], '20')
        self.assertEqual(env['RAG_STRICT_RERANK'], 'true')
        self.assertEqual(set(env), {'RAG_BM25_INDEX', 'RAG_DENSE_INDEX', 'RAG_QDRANT_PATH',
                                    'RAG_CHUNKS', 'RAG_TOP_K', 'RAG_STRICT_RERANK'})

    def test_existing_output_is_not_overwritten_and_unsupported_selection_fails(self):
        with self.assertRaisesRegex(ValueError, 'already exists'):
            prepare(self.runtime, self.config, self.chunks, self.root / 'cache')
        value = json.loads(self.config.read_text(encoding='utf-8')); value['hybrid']['weights'] = [1, 1]
        self.config.write_text(json.dumps(value), encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'not supported'):
            prepare(self.root / 'new', self.config, self.chunks, self.root / 'cache')
        self.assertFalse((self.root / 'new').exists())


if __name__ == '__main__': unittest.main()
