"""VLRA-54/55: compare Hybrid and Hybrid + Reranker on the same candidates."""
from __future__ import annotations

import argparse
import copy
import json
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

from scripts.eval_retrieval import ROOT, environment, fingerprint, percentile, validate_cases, validate_output
from team2_rag.reranker import BGEScorer, rerank_with_details


def unit_groups(case):
    """Use reviewed equivalent subchunks; legacy gold IDs remain separate units."""
    return case.get("relevant_unit_groups", [[cid] for cid in case["gold_chunk_ids"]])


def validate_dataset(cases, corpus, *, exploratory=False):
    validate_cases(cases, set(corpus))
    for case in cases:
        if case.get("split") == "test" or (not exploratory and case.get("split") != "dev"):
            raise ValueError("Use Dev rows only; unsplit data requires --exploratory")
        groups = unit_groups(case)
        if not isinstance(groups, list) or any(
            not isinstance(g, list) or not g or any(not isinstance(cid, str) or not cid for cid in g)
            for g in groups
        ):
            raise ValueError("relevant_unit_groups must be an array of non-empty ID arrays")
        ids = [cid for group in groups for cid in group]
        if len(ids) != len(set(ids)) or set(ids) - set(corpus):
            raise ValueError("Gold groups overlap or reference unknown chunks")
        if bool(groups) != (case["expected_status"] == "answered") or set(case["gold_chunk_ids"]) - set(ids):
            raise ValueError("Gold groups must cover gold_chunk_ids and match expected_status")
        if not exploratory and "relevant_unit_groups" not in case:
            raise ValueError("Dev evaluation requires reviewed relevant_unit_groups")


def metrics(ids, groups):
    """Each legal unit counts once, even when several equivalent chunks match."""
    keys = ("recall_at_5", "recall_at_10", "recall_at_20", "mrr_at_20", "top1_hit")
    if not groups:
        return dict.fromkeys(keys)
    gold = set().union(*map(set, groups))
    recall = {f"recall_at_{k}": sum(bool(set(ids[:k]) & set(g)) for g in groups) / len(groups)
              for k in (5, 10, 20)}
    return dict(**recall, mrr_at_20=next((1 / i for i, cid in enumerate(ids[:20], 1) if cid in gold), 0.0),
                top1_hit=float(bool(ids and ids[0] in gold)))


def latency(values):
    return dict(samples=len(values), p50=percentile(values, .5), p95=percentile(values, .95))


def summarize(rows):
    """Keep failures in the report and use the same successful pairs for deltas."""
    paired = [r for r in rows if r["status"] == "OK" and r["before"]["recall_at_5"] is not None]
    result = dict(total=len(rows), paired_answerable=len(paired),
                  unanswerable=sum(not r["groups"] for r in rows),
                  retrieval_errors=sum(r["status"] == "RETRIEVAL_ERROR" for r in rows),
                  rerank_errors=sum(r["status"] == "RERANK_ERROR" for r in rows))
    result["failure_rate"] = (result["retrieval_errors"] + result["rerank_errors"]) / len(rows) if rows else None
    keys = metrics([], []).keys()
    for name in ("before", "after"):
        result[name] = {k: sum(r[name][k] for r in paired) / len(paired) if paired else None for k in keys}
    result["delta"] = {k: result["after"][k] - result["before"][k] if paired else None for k in keys}
    for name in ("promoted", "demoted", "mixed", "unchanged"):
        count = sum(r["impact"] == name for r in paired)
        result[name] = dict(count=count, rate=count / len(paired) if paired else None)
    result["latency_ms"] = {
        stage: latency([r[stage] for r in rows if stage in r])
        for stage in ("retrieval_ms", "rerank_ms", "total_ms")
    }
    return result


def evaluate(retriever, scorer, cases, corpus):
    rows = []
    for case in cases:
        row = dict(id=case["id"], question=case["question"], groups=unit_groups(case), status="OK")
        start = time.perf_counter()
        try:
            pool = retriever.retrieve(case["question"], top_k=20)
            row["retrieval_ms"] = (time.perf_counter() - start) * 1000
            validate_output(pool, case["question"], "hybrid_rrf", corpus)
            # Retain the original pool: reranking must change order only.
            original = copy.deepcopy(pool)
            before_ids = [r["chunk_id"] for r in original["results"]]
            row.update(before=metrics(before_ids, row["groups"]), candidates=original["results"])
        except Exception as exc:
            row.update(status="RETRIEVAL_ERROR", error_type=type(exc).__name__, error=str(exc),
                       retrieval_failed_ms=(time.perf_counter() - start) * 1000)
            rows.append(row)
            continue
        rerank_start = time.perf_counter()
        try:
            details = rerank_with_details(pool, scorer=scorer, strict=True)
            row["rerank_ms"] = (time.perf_counter() - rerank_start) * 1000
            after_ids = [r["chunk_id"] for r in details.output["results"]]
            by_id = {r["chunk_id"]: r for r in original["results"]}
            if (len(after_ids) != len(before_ids) or set(after_ids) != set(before_ids)
                    or any(r != by_id[r["chunk_id"]] for r in details.output["results"])):
                raise ValueError("Reranker changed the candidate pool or metadata")
            row.update(after=metrics(after_ids, row["groups"]), reranked_ids=after_ids, scores=details.scores)
            # A query may gain one required unit and lose another. Keep both events.
            before_hits = {i for i, g in enumerate(row["groups"]) if set(g) & set(before_ids[:5])}
            after_hits = {i for i, g in enumerate(row["groups"]) if set(g) & set(after_ids[:5])}
            gained, lost = sorted(after_hits - before_hits), sorted(before_hits - after_hits)
            row.update(gained_groups=gained, lost_groups=lost,
                       impact="mixed" if gained and lost else "promoted" if gained else "demoted" if lost else "unchanged",
                       missing_from_pool=[i for i, g in enumerate(row["groups"]) if not set(g) & set(before_ids)])
        except Exception as exc:
            row.update(status="RERANK_ERROR", error_type=type(exc).__name__, error=str(exc),
                       rerank_failed_ms=(time.perf_counter() - rerank_start) * 1000)
        row["total_ms"] = (time.perf_counter() - start) * 1000
        rows.append(row)
    return dict(status="ERROR" if any(r["status"] != "OK" for r in rows) else "COMPLETE",
                summary=summarize(rows), cases=rows)


def build_retriever(args, corpus):
    """Reuse Team 1 indexes and the current pipeline adapter; never rebuild them."""
    bm, dense = [json.loads((p / "index_manifest.json").read_text(encoding="utf-8"))
                 for p in (args.bm25_index, args.dense_index)]
    if (bm["index_version"] != dense["index_version"] or set(bm["chunk_ids"]) != set(corpus)
            or set(dense["chunk_ids"]) != set(corpus)):
        raise ValueError("BM25, Dense and corpus must share the same snapshot")
    from qdrant_client import QdrantClient
    from team1_data.retrieval import BM25Retriever, DenseRetriever, HybridRetriever, SentenceTransformerEmbedder
    from team2_rag.pipeline import BM25SearchAdapter

    client = (QdrantClient(path=str(args.qdrant_path)) if args.qdrant_path else
              QdrantClient(url=args.qdrant_url, timeout=5))
    try:
        embedder = SentenceTransformerEmbedder(
            name=dense["embedding_model"], revision=dense["embedding_revision"],
            query_prefix=dense.get("query_prefix", ""), passage_prefix=dense.get("passage_prefix", ""), device="cpu")
        sparse = BM25Retriever.load(args.bm25_index, args.chunks)
        vectors = DenseRetriever.connect(args.dense_index, embedder, client=client)
        return HybridRetriever(BM25SearchAdapter(sparse), vectors), client
    except BaseException:
        client.close()
        raise


def markdown(report):
    lines = ["# Đánh giá tác động của Reranker", "", f"Trạng thái: {report['status']}.",
             f"Phạm vi: {report['scope']}.", "",
             "So sánh Hybrid top 20 và BGE rerank trên cùng ứng viên; không gọi LLM.",
             "Đây là ablation retrieval, chưa phải đánh giá B0/T0 toàn hệ thống.", ""]
    if "summary" not in report:
        return "\n".join(lines + [f"Chưa chạy được: {report.get('error', 'thiếu dữ liệu')}.", ""])
    s = report["summary"]
    lines += [f"Tổng {s['total']} câu; {s['paired_answerable']} cặp answerable thành công; "
              f"{s['unanswerable']} câu không tính Recall/MRR; "
              f"{s['retrieval_errors']} lỗi retrieval, {s['rerank_errors']} lỗi reranker.", "",
              "Metric tính trên cùng các cặp thành công. Run có lỗi không được dùng để xác nhận đạt mục tiêu.", "",
              "| Chỉ số | Hybrid | Hybrid + Reranker | Chênh lệch |", "| --- | ---: | ---: | ---: |"]
    def fmt(value):
        return "N/A" if value is None else f"{value:.4f}"
    for k in s["before"]:
        lines.append(f"| {k} | {fmt(s['before'][k])} | {fmt(s['after'][k])} | {fmt(s['delta'][k])} |")
    lines += ["", "Recall tính theo gold unit group; top1_hit chỉ đo trúng căn cứ, không chấm câu trả lời.", "",
              "| Độ trễ (ms) | Mẫu | p50 | p95 |", "| --- | ---: | ---: | ---: |"]
    for stage, values in s["latency_ms"].items():
        lines.append(f"| {stage} | {values['samples']} | {fmt(values['p50'])} | {fmt(values['p95'])} |")
    lines += ["", "Độ trễ trên là các bước thành công, không gồm setup/warm-up. Thời gian lỗi nằm trong JSON; "
              "total_ms chỉ gồm retrieval, kiểm tra và rerank, chưa phải latency toàn hệ thống.", "",
              "| Tác động ở top 5 | Số câu | Tỷ lệ trên cặp answerable |", "| --- | ---: | ---: |"]
    for name in ("promoted", "demoted", "mixed", "unchanged"):
        lines.append(f"| {name} | {s[name]['count']} | {fmt(s[name]['rate'])} |")
    lines += ["", "## Các ca cần xem lại", "",
              "Các dấu hiệu dưới đây phục vụ review; chưa khẳng định nguyên nhân lỗi ngữ nghĩa.", ""]
    for row in report["cases"]:
        if row["status"] != "OK":
            lines.append(f"- {row['id']}: {row['status']} ({row['error_type']}).")
        elif row["groups"] and (row["after"]["recall_at_5"] < 1 or row["impact"] == "mixed"):
            lines.append(f"- {row['id']}: {row['impact']}; nhóm tăng {row['gained_groups']}, "
                         f"nhóm mất {row['lost_groups']}, nhóm thiếu từ Hybrid top 20 {row['missing_from_pool']}.")
    lines += ["", "Dùng JSON để xem câu hỏi, ứng viên, thứ tự và điểm BGE. "
              "Chưa chốt cấu hình RAG: Người 2 tổng hợp thêm phân tích lỗi và Context Builder cho VLRA-58.", ""]
    return "\n".join(lines)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--golden", type=Path, required=True)
    parser.add_argument("--chunks", type=Path, default=ROOT / "data/doanh-nghiep/processed/chunks.jsonl")
    parser.add_argument("--bm25-index", type=Path, required=True)
    parser.add_argument("--dense-index", type=Path, required=True)
    connection = parser.add_mutually_exclusive_group()
    connection.add_argument("--qdrant-path", type=Path)
    connection.add_argument("--qdrant-url", default="http://localhost:6333")
    parser.add_argument("--output", type=Path, required=True, help="JSON report; Markdown uses the same stem")
    parser.add_argument("--exploratory", action="store_true", help="Allow unsplit legacy gold; not an acceptance run")
    args = parser.parse_args(argv)
    report = dict(status="BLOCKED", scope="exploratory" if args.exploratory else "dev",
                  run_at=datetime.now(timezone.utc).isoformat(), environment=environment(),
                  config=dict(candidate_k=20, context_cutoff=5, rrf_k=60, weights=[1, 1],
                              reranker="BAAI/bge-reranker-v2-m3", device="cpu", batch_size=2, max_length=512))
    client = None
    try:
        report["head"] = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
        report["dirty"] = bool(subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT))
        cases = json.loads(args.golden.read_text(encoding="utf-8"))
        chunks = [json.loads(line) for line in args.chunks.read_text(encoding="utf-8").splitlines() if line.strip()]
        corpus = {c["chunk_id"]: c for c in chunks}
        if len(corpus) != len(chunks):
            raise ValueError("Duplicate corpus chunk IDs")
        validate_dataset(cases, corpus, exploratory=args.exploratory)
        report["sources"] = [fingerprint(p) for p in (args.golden, args.chunks, Path(__file__),
                             ROOT / "team2_rag/reranker.py", ROOT / "team2_rag/pipeline.py")]
        report["sources"] += [fingerprint(p) for p in sorted((ROOT / "team1_data/retrieval").glob("*.py"))]
        report["indexes"] = []
        for path in (args.bm25_index, args.dense_index):
            manifest_path = path / "index_manifest.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            report["indexes"].append(dict(**fingerprint(manifest_path),
                                         manifest={k: v for k, v in manifest.items() if k != "chunk_ids"}))
        start = time.perf_counter()
        retriever, client = build_retriever(args, corpus)
        scorer = BGEScorer()
        scorer([("Khởi động mô hình", "Đây là nội dung khởi động mô hình.")])
        warmup_start = time.perf_counter()
        warmup = retriever.retrieve(cases[0]["question"], top_k=20)
        validate_output(warmup, cases[0]["question"], "hybrid_rrf", corpus)
        report["retrieval_warmup_ms"] = (time.perf_counter() - warmup_start) * 1000
        report["setup_ms"] = (time.perf_counter() - start) * 1000
        report["reranker_revision"] = getattr(scorer._model.config, "_commit_hash", None)
        report.update(evaluate(retriever, scorer, cases, corpus))
    except Exception as exc:
        report.update(status="BLOCKED", error_type=type(exc).__name__, error=str(exc))
    finally:
        if client is not None:
            client.close()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    args.output.with_suffix(".md").write_text(markdown(report), encoding="utf-8")
    print(json.dumps({k: report.get(k) for k in ("status", "scope", "summary", "error")}, ensure_ascii=False))
    return 0 if report["status"] == "COMPLETE" else 2 if report["status"] == "BLOCKED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
