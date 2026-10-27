"""Reproducible retrieval evaluation; no LLM calls, tuning or hidden fallback.

The evaluate() function accepts any object implementing retrieve(question, top_k).
Empty-gold cases are observed but excluded from Recall/MRR, not scored as perfect.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib
import importlib.metadata
import json
import math
import platform
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def percentile(values, quantile):
    if not values:
        return None
    values = sorted(values)
    position = (len(values) - 1) * quantile
    low, high = math.floor(position), math.ceil(position)
    return values[low] + (values[high] - values[low]) * (position - low)


def metrics(ids, gold):
    gold = set(gold)
    if not gold:
        return dict(recall_at_5=None, recall_at_20=None, rr_at_10=None)
    return dict(recall_at_5=len(gold.intersection(ids[:5])) / len(gold),
                recall_at_20=len(gold.intersection(ids[:20])) / len(gold),
                rr_at_10=next((1 / rank for rank, cid in enumerate(ids[:10], 1) if cid in gold), 0.0))


def validate_cases(cases, corpus_ids):
    if not isinstance(cases, list) or not cases:
        raise ValueError("golden must be a non-empty array")
    seen, questions = set(), set()
    for case in cases:
        if not isinstance(case, dict):
            raise ValueError("golden rows must be objects")
        cid, question, gold = case.get("id"), case.get("question"), case.get("gold_chunk_ids")
        if not isinstance(cid, str) or not cid or cid in seen:
            raise ValueError("golden IDs must be non-empty unique strings")
        if not isinstance(question, str) or not 1 <= len(question.strip()) <= 4000 or question.strip() in questions:
            raise ValueError("golden questions must be valid and unique")
        if not isinstance(gold, list) or not all(isinstance(x, str) for x in gold) or len(set(gold)) != len(gold):
            raise ValueError("gold_chunk_ids must be a unique string array")
        status = case.get("expected_status")
        if status not in ("answered", "insufficient_context") or bool(gold) != (status == "answered"):
            raise ValueError("gold IDs do not match expected_status")
        if set(gold) - corpus_ids:
            raise ValueError(f"unknown gold IDs in case {cid}")
        seen.add(cid)
        questions.add(question.strip())


def validate_output(output, question, method, corpus=None):
    from jsonschema import Draft202012Validator, FormatChecker
    schema = json.loads((ROOT / "contracts/v0.1/retrieval_output.schema.json").read_text(encoding="utf-8"))
    Draft202012Validator(schema, format_checker=FormatChecker()).validate(output)
    rows = output["results"]
    if output["question"] != question.strip() or len(rows) > 20:
        raise ValueError("question mismatch or top_k limit violated")
    if [r["rank"] for r in rows] != list(range(1, len(rows) + 1)):
        raise ValueError("ranks must be contiguous and one-based")
    if len({r["chunk_id"] for r in rows}) != len(rows):
        raise ValueError("duplicate candidate chunk_id")
    scores = [r["score"] for r in rows]
    if not all(math.isfinite(s) for s in scores) or scores != sorted(scores, reverse=True):
        raise ValueError("scores must be finite and descending")
    for row in rows:
        if row["retrieval_method"] != method:
            raise ValueError("retrieval_method mismatch")
        if method == "bm25" and row["score"] <= 0:
            raise ValueError("BM25 must remove non-positive scores")
        if method == "dense" and not -1 - 1e-6 <= row["score"] <= 1 + 1e-6:
            raise ValueError("cosine score outside [-1,1]")
        if corpus is not None:
            source = corpus.get(row["chunk_id"])
            if source is None or any(row[k] != source.get(k) for k in row if k not in ("score", "rank", "retrieval_method")):
                raise ValueError("candidate provenance/content mismatch")


def aggregate(rows):
    scored = [r for r in rows if r["status"] == "OK" and r["recall_at_20"] is not None]
    latencies = [r["elapsed_ms"] for r in rows if r["status"] == "OK"]
    return dict(counts=dict(total=len(rows), scored=len(scored),
                            errors=sum(r["status"] == "ERROR" for r in rows),
                            empty_gold=sum(not r["expected_chunk_ids"] for r in rows)),
                metrics={key: sum(r[field] for r in scored) / len(scored) if scored else None
                         for key, field in [("recall_at_5", "recall_at_5"), ("recall_at_20", "recall_at_20"),
                                            ("mrr_at_10", "rr_at_10")]},
                latency_ms=dict(p50=percentile(latencies, .5), p95=percentile(latencies, .95),
                                samples=len(latencies), percentile="linear interpolation", scope="retrieve only; successful calls"))


def evaluate(retriever, cases, *, method, groups=None, corpus=None):
    rows = []
    for case in cases:
        row = dict(id=case["id"], question=case["question"], group=(groups or {}).get(case["id"], "unclassified"),
                   expected_chunk_ids=case["gold_chunk_ids"], status="OK")
        start = time.perf_counter()
        try:
            output = retriever.retrieve(case["question"], top_k=20)
            row["elapsed_ms"] = (time.perf_counter() - start) * 1000
            validate_output(output, case["question"], method, corpus)
            ids = [r["chunk_id"] for r in output["results"]]
            row.update(metrics(ids, case["gold_chunk_ids"]))
            row["results"] = [{k: r[k] for k in ("chunk_id", "rank", "score", "retrieval_method")}
                              for r in output["results"]]
        except Exception as exc:
            row.update(status="ERROR", elapsed_ms=(time.perf_counter() - start) * 1000,
                       error_type=type(exc).__name__, error=str(exc), **metrics([], []))
        rows.append(row)
    result = dict(status="ERROR" if any(r["status"] == "ERROR" for r in rows) else "COMPLETE",
                  method=method, **aggregate(rows), cases=rows)
    result["groups"] = {group: aggregate([r for r in rows if r["group"] == group]) for group in sorted({r["group"] for r in rows})}
    return result


def environment():
    packages = {}
    for name in ("bm25s", "underthesea", "numpy", "qdrant-client", "jsonschema", "torch", "sentence-transformers"):
        try:
            packages[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            packages[name] = None
    return dict(python=platform.python_version(), platform=platform.platform(), packages=packages)


def fingerprint(path):
    path = Path(path)
    try:
        label = path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        label = path.name
    return dict(path=label, sha256=hashlib.sha256(path.read_bytes()).hexdigest())


def make_retriever(args):
    if args.factory:
        module, name = args.factory.split(":", 1)
        return getattr(importlib.import_module(module), name)(args)
    if not args.index:
        raise ValueError("--index is required for built-in adapters")
    if args.method == "bm25":
        from team1_data.retrieval.bm25 import BM25Retriever
        return BM25Retriever.load(args.index, args.chunks)
    if args.method == "dense":
        from team1_data.retrieval.dense import DenseRetriever
        from team1_data.retrieval.embedding import SentenceTransformerEmbedder
        if not args.revision:
            raise ValueError("--revision must pin the real embedding model commit")
        return DenseRetriever.connect(args.index, SentenceTransformerEmbedder(args.model, revision=args.revision),
                                      url=args.qdrant_url)
    raise ValueError("Hybrid runtime is not delivered; provide --factory module:function from its owner")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--method", required=True, choices=("bm25", "dense", "hybrid_rrf"))
    parser.add_argument("--golden", type=Path, required=True)
    parser.add_argument("--groups", type=Path)
    parser.add_argument("--chunks", type=Path, default=ROOT / "data/doanh-nghiep/processed/chunks.jsonl")
    parser.add_argument("--index", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--factory", help="owner adapter module:function(args) -> retriever")
    parser.add_argument("--model", default="AITeamVN/Vietnamese_Embedding")
    parser.add_argument("--revision")
    parser.add_argument("--qdrant-url", default="http://localhost:6333")
    args = parser.parse_args(argv)
    report = dict(report_version=1, run_at=datetime.now(timezone.utc).isoformat(), method=args.method,
                  status="BLOCKED", environment=environment())
    try:
        report["head"] = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
        report["dirty"] = bool(subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT))
        report["sources"] = [fingerprint(p) for p in [args.golden, args.chunks, Path(__file__),
                              ROOT / "contracts/v0.1/retrieval_output.schema.json"]]
        report["runtime_sources"] = [fingerprint(p) for p in sorted((ROOT / "team1_data/retrieval").glob("*.py"))]
        if args.groups:
            report["sources"].append(fingerprint(args.groups))
        cases = json.loads(args.golden.read_text(encoding="utf-8"))
        chunks = [json.loads(line) for line in args.chunks.read_text(encoding="utf-8").splitlines() if line.strip()]
        corpus = {chunk["chunk_id"]: chunk for chunk in chunks}
        if len(corpus) != len(chunks):
            raise ValueError("corpus contains duplicate IDs")
        validate_cases(cases, set(corpus))
        groups = json.loads(args.groups.read_text(encoding="utf-8"))["groups"] if args.groups else {}
        if args.groups and any(c["id"] not in groups for c in cases):
            raise ValueError("query groups sidecar does not cover every case")
        start = time.perf_counter()
        retriever = make_retriever(args)
        report["setup_ms"] = (time.perf_counter() - start) * 1000
        manifest_path = args.index / "index_manifest.json" if args.index else None
        manifest = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path and manifest_path.exists() else {}
        report["index_version"] = manifest.get("index_version")
        report["model"] = dict(name=manifest.get("embedding_model"), revision=manifest.get("embedding_revision"))
        report["corpus_chunk_count"] = len(chunks)
        report["index_manifest"] = {k: v for k, v in manifest.items() if k != "chunk_ids"}
        if manifest_path and manifest_path.exists():
            report["manifest_source"] = fingerprint(manifest_path)
        report.update(evaluate(retriever, cases, method=args.method, groups=groups, corpus=corpus))
        code = 0 if report["status"] == "COMPLETE" else 1
    except Exception as exc:
        report.update(status="BLOCKED", error_type=type(exc).__name__, error=str(exc))
        code = 2
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps({k: report.get(k) for k in ("status", "method", "counts", "metrics", "error_type")}, ensure_ascii=False))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
