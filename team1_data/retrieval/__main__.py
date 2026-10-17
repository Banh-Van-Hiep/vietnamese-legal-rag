"""CLI: build hoặc truy vấn index BM25 / Dense (python -m team1_data.retrieval)."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .common import DEFAULT_CHUNKS, DEFAULT_QDRANT_URL


def _print(output: dict) -> None:
    for r in output["results"]:
        print(f'{r["rank"]:>2}  {r["score"]:6.3f}  {r["chunk_id"]}')


def _embedder(args):
    from .embedding import SentenceTransformerEmbedder

    return SentenceTransformerEmbedder(args.model, revision=args.revision, query_prefix=args.query_prefix,
                                       passage_prefix=args.passage_prefix)


def _main(argv: list[str] | None = None) -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="Build or query the BM25 / dense index.")
    sub = parser.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build", help="build the BM25 index from chunks.jsonl")
    b.add_argument("--chunks", type=Path, default=DEFAULT_CHUNKS)
    b.add_argument("--out", type=Path, required=True, help="e.g. data/index/bm25/2026-10-17-01")
    q = sub.add_parser("query", help="query a saved BM25 index")
    q.add_argument("question")
    q.add_argument("--index", type=Path, required=True)
    q.add_argument("--chunks", type=Path, default=DEFAULT_CHUNKS)
    q.add_argument("--top-k", type=int, default=5)

    from .embedding import DEFAULT_MODEL

    dense_args = argparse.ArgumentParser(add_help=False)
    dense_args.add_argument("--qdrant-url", default=DEFAULT_QDRANT_URL)
    dense_args.add_argument("--model", default=DEFAULT_MODEL)
    dense_args.add_argument("--revision", default=None, help="Hugging Face commit hash; pin it for a real index")
    dense_args.add_argument("--query-prefix", default="")
    dense_args.add_argument("--passage-prefix", default="")
    db = sub.add_parser("dense-build", parents=[dense_args], help="embed chunks and upsert them into Qdrant")
    db.add_argument("--chunks", type=Path, default=DEFAULT_CHUNKS)
    db.add_argument("--out", type=Path, required=True, help="e.g. data/index/dense/2026-10-17-01")
    dq = sub.add_parser("dense-query", parents=[dense_args], help="query a built dense index")
    dq.add_argument("question")
    dq.add_argument("--index", type=Path, required=True)
    dq.add_argument("--top-k", type=int, default=5)
    args = parser.parse_args(argv)

    if args.cmd in ("build", "query"):
        from .bm25 import BM25Retriever

        if args.cmd == "build":
            retriever = BM25Retriever.from_jsonl(args.chunks)
            retriever.save(args.out)
            print(f"[OK] {len(retriever.chunks)} chunks -> {args.out}")
        else:
            _print(BM25Retriever.load(args.index, args.chunks).retrieve(args.question, args.top_k))
        return

    from qdrant_client import QdrantClient

    from .dense import DenseRetriever

    if args.cmd == "dense-build":
        retriever = DenseRetriever.from_jsonl(args.chunks, embedder=_embedder(args),
                                              client=QdrantClient(url=args.qdrant_url), index_version=args.out.name)
        retriever.save(args.out)
        print(f"[OK] {len(retriever.chunks)} chunks -> {retriever.collection} + {args.out}")
    else:
        retriever = DenseRetriever.connect(args.index, _embedder(args), url=args.qdrant_url)
        _print(retriever.retrieve(args.question, args.top_k))


if __name__ == "__main__":
    _main()
