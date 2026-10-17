"""CLI: build hoặc truy vấn index BM25 (python -m team1_data.retrieval)."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .bm25 import DEFAULT_CHUNKS, BM25Retriever


def _main(argv: list[str] | None = None) -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="Build or query the BM25 index.")
    sub = parser.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build", help="build the index from chunks.jsonl")
    b.add_argument("--chunks", type=Path, default=DEFAULT_CHUNKS)
    b.add_argument("--out", type=Path, required=True, help="e.g. data/index/bm25/2026-10-17-01")
    q = sub.add_parser("query", help="query a saved index")
    q.add_argument("question")
    q.add_argument("--index", type=Path, required=True)
    q.add_argument("--chunks", type=Path, default=DEFAULT_CHUNKS)
    q.add_argument("--top-k", type=int, default=5)
    args = parser.parse_args(argv)

    if args.cmd == "build":
        retriever = BM25Retriever.from_jsonl(args.chunks)
        retriever.save(args.out)
        print(f"[OK] {len(retriever.chunks)} chunks -> {args.out}")
    else:
        output = BM25Retriever.load(args.index, args.chunks).retrieve(args.question, args.top_k)
        for r in output["results"]:
            print(f'{r["rank"]:>2}  {r["score"]:6.2f}  {r["chunk_id"]}')


if __name__ == "__main__":
    _main()
