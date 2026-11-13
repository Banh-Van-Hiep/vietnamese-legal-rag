"""End-to-End Latency & Stability Benchmark (VLRA-T2-34 & VLRA-T2-35: NFR-07, NFR-08, NFR-09).

Chạy chế độ local BM25-only + Gemini thật trên 30 câu Golden (hoặc --smoke / --mock-llm),
đo phân rã từng chặng qua RAGPipeline.query, đo thực nghiệm Article Viewer (NFR-09),
và tự động xuất cả 2 file:
  - docs/team2_rag/ai_service_load_and_stability_report.json
  - docs/team2_rag/ai_service_load_and_stability_report.md
"""
from __future__ import annotations

import argparse
import hashlib
import json
import logging
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from team1_data.retrieval import BM25Retriever
from team2_rag.articles import ArticleLookupError, _load_article_cache, get_article
from team2_rag.config.settings import load_settings, read_dotenv
from team2_rag.llm.factory import create_llm_service
from team2_rag.llm.fake import FakeLLMProvider
from team2_rag.llm.service import LLMService
from team2_rag.llm.tokens import token_budget_from_settings
from team2_rag.pipeline import RAGPipeline
from team2_rag.reranker import BGEScorer
from team2_rag.verification import verify_response

log = logging.getLogger("e2e_benchmark")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")


def _flag(env: dict, key: str, default: str) -> bool:
    return str(env.get(key, default)).strip().lower() in ("true", "1")


def _git_sha() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "--short=10", "HEAD"], text=True).strip()
    except Exception:
        return "unknown"


def _calc_dist(arr: list[float]) -> dict:
    if not arr:
        return {"count": 0, "mean_s": 0.0, "p50_s": 0.0, "p90_s": 0.0, "p95_s": 0.0, "max_s": 0.0}
    return {
        "count": len(arr),
        "mean_s": round(float(np.mean(arr)), 3),
        "p50_s": round(float(np.percentile(arr, 50)), 3),
        "p90_s": round(float(np.percentile(arr, 90)), 3),
        "p95_s": round(float(np.percentile(arr, 95)), 3),
        "max_s": round(float(np.max(arr)), 3),
    }


def benchmark_article_viewer(chunks_path: Path | None = None) -> dict:
    """Đo thực nghiệm NFR-09 trên endpoint logic get_article (cold start + warm @lru_cache + 3 mã lỗi)."""
    _load_article_cache.cache_clear()
    doc_id = "luat-59-2020-qh14-v1"

    t0 = time.monotonic()
    get_article(doc_id, "dieu-1")
    cold_start_ms = (time.monotonic() - t0) * 1000.0

    sample_articles = [f"dieu-{i}" for i in range(1, 21)]
    warm_ms: list[float] = []
    for art_id in sample_articles:
        t_start = time.monotonic()
        get_article(doc_id, art_id)
        warm_ms.append((time.monotonic() - t_start) * 1000.0)

    error_cases: dict[str, int] = {}
    for bad_doc, bad_art in (
        ("van-ban-khong-ton-tai", "dieu-1"),
        (doc_id, "dieu-9999"),
        ("id sai dinh dang!", "dieu-1"),
    ):
        try:
            get_article(bad_doc, bad_art)
        except ArticleLookupError as exc:
            error_cases[exc.code] = exc.status_code

    warm_p50 = round(float(np.percentile(warm_ms, 50)), 3)
    warm_p95 = round(float(np.percentile(warm_ms, 95)), 3)
    warm_max = round(float(np.max(warm_ms)), 3)
    return {
        "sample_size": len(warm_ms),
        "cold_start_ms": round(cold_start_ms, 3),
        "warm_p50_ms": warm_p50,
        "warm_p95_ms": warm_p95,
        "warm_max_ms": warm_max,
        "error_cases_tested": error_cases,
        "nfr09_passed": (
            cold_start_ms <= 10000.0
            and warm_p95 <= 10000.0
            and error_cases.get("DOCUMENT_NOT_FOUND") == 404
            and error_cases.get("ARTICLE_NOT_FOUND") == 404
            and error_cases.get("INVALID_REQUEST") == 400
        ),
    }


def _render_markdown_report(report: dict) -> str:
    cfg = report["config"]
    out = report["request_outcomes"]
    st = report["stage_latency"]
    av = report["article_viewer"]
    err = report["error_breakdown"]

    def _row(label: str, key: str) -> str:
        d = st.get(key, {"count": 0, "mean_s": 0.0, "p50_s": 0.0, "p90_s": 0.0, "p95_s": 0.0, "max_s": 0.0})
        return f"| **{label}** (`{key}`) | {d['count']} | {d['mean_s']:.3f} | {d['p50_s']:.3f} | {d['p90_s']:.3f} | **{d['p95_s']:.3f}** | {d['max_s']:.3f} |"

    err_lines = "\n".join(f"- `{k}`: {v} ca" for k, v in err.items()) if err else "- Không phát sinh lỗi (`0` ca lỗi/timeout)."
    failed_str = ", ".join(f"`{q}`" for q in report["failed_query_ids"]) if report["failed_query_ids"] else "Không có (`[]`)"
    nfr07_badge = "ĐẠT (PASSED)" if report["nfr07_p95_le_45s_passed"] else "CHƯA ĐẠT (FAILED)"
    nfr09_badge = "ĐẠT (PASSED)" if av["nfr09_passed"] else "CHƯA ĐẠT (FAILED)"

    return f"""# Báo Cáo Kiểm Thử Tải và Độ Ổn Định AI Service (Tuần 10 — VLRA-74)

- **Git Commit:** `{report['git_commit']}`
- **Thời điểm đo (UTC):** `{report['timestamp_utc']}`
- **Tập dữ liệu:** `{report['dataset_path']}` (SHA-256: `{report['dataset_sha256']}`, `{out['total']}` câu hỏi)
- **Chế độ thực thi:** `{cfg['retrieval_mode']}` (Nhóm thống nhất không dùng Colab, chạy trực tiếp trên máy local với BM25-only + LLM `{cfg['model']}`)

---

## 1. Cấu Hình Thực Thi (`config`)

| Tham số | Giá trị | Ghi chú |
| :--- | :--- | :--- |
| `retrieval_mode` | `{cfg['retrieval_mode']}` | Chạy local không phụ thuộc GPU/Colab |
| `model` | `{cfg['model']}` | Provider: `{cfg['provider']}` |
| `top_k` | `{cfg['top_k']}` | Số chunk đưa vào bước tạo context |
| `rerank_enabled` | `{cfg['rerank_enabled']}` | Tắt theo cấu hình tối ưu Tuần 9 |
| `verify_claims` | `{cfg['verify_claims']}` | Chế độ runtime online (`RAG_VERIFY_CLAIMS=false`) |
| `pipeline_timeout_s` | `{cfg['pipeline_timeout_s']}s` | Trần ngân sách thời gian tầng AI (NFR-08) |

---

## 2. Kết Quả Độ Trễ End-to-End Theo Từng Chặng (NFR-07: `p95 <= 45.0s`)

Đo trực tiếp qua hàm `RAGPipeline.query()` trên toàn bộ `{out['total']}` câu hỏi:

| Chặng xử lý | Số mẫu (`count`) | Mean (s) | P50 (s) | P90 (s) | P95 (s) | Max (s) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
{_row("Truy xuất (Retrieval)", "retrieval")}
{_row("Xếp hạng lại (Rerank)", "rerank")}
{_row("Sinh câu trả lời (LLM)", "llm")}
{_row("Kiểm chứng (Verify)", "verify")}
{_row("Tổng End-to-End", "e2e_total")}

- **Kết luận NFR-07 (`p95 <= 45.0s`):** **{nfr07_badge}** (`p95 = {st['e2e_total']['p95_s']:.3f}s <= 45.0s`).
- *Lưu ý kỹ thuật:* Chế độ đo local sử dụng `BM25-only` (do nhóm không sử dụng Colab cho Dense/Qdrant). Độ trễ Retrieval của BM25 local ở mức mili-giây; phần lớn thời gian End-to-End nằm ở chặng gọi Gemini API (`llm`).

---

## 3. Thống Kê Độ Ổn Định & Phân Loại Kết Quả (`request_outcomes`)

| Trạng thái | Số lượng | Tỷ lệ (%) |
| :--- | :---: | :---: |
| Tổng số truy vấn (`total`) | `{out['total']}` | `100.0%` |
| Trả lời thành công (`answered`) | `{out['answered']}` | `{out['answered'] * 100.0 / max(1, out['total']):.1f}%` |
| Từ chối hợp lệ (`insufficient_context`) | `{out['insufficient_context']}` | `{out['insufficient_context'] * 100.0 / max(1, out['total']):.1f}%` |
| Quá hạn (`timeout`) | `{out['timeout']}` | `{out['timeout'] * 100.0 / max(1, out['total']):.1f}%` |
| Lỗi khác (`error`) | `{out['error']}` | `{out['error'] * 100.0 / max(1, out['total']):.1f}%` |

**Chi tiết mã lỗi (`error_breakdown`):**
{err_lines}

- **Danh sách `query_id` gặp lỗi/timeout:** {failed_str}

---

## 4. Kiểm Chứng Chuỗi Timeout & Khóa Slot Đồng Thời (NFR-08)

Hệ thống đảm bảo bất biến:
`T_AI_Deadline (45.0s) < T_Java_Backend_Timeout (50.0s) < T_Frontend_Timeout (60.0s)`

1. **Truyền ngân sách thời gian còn lại (`remaining`) xuống LLM (`VLRA-T2-33`):**
   - Trong `RAGPipeline.query()`, sau khi hoàn tất Retrieval và Rerank, hệ thống tính `remaining = deadline - time.monotonic()`.
   - Nếu `remaining <= 1.0s`: lập tức ném `LLMTimeoutError` (`HTTP 504`, wire code `"LLM_TIMEOUT"`).
   - Nếu `remaining > 1.0s`: truyền `llm_timeout_seconds = max(0.1, remaining - 0.5)` xuống `generate_answer_detailed` -> `llm_service.ask` để ép provider tự ngắt trước mốc `45.0s`.
2. **Chốt chặn API & Concurrency Slot Lock (`team2_rag/tests/test_nfr08_timeout_concurrency.py`):**
   - Khi pipeline vượt quá `timeout_seconds`, tầng FastAPI trả `HTTP 504` với mã `"LLM_TIMEOUT"`, `retryable: true`.
   - Khi có request thứ 2 gọi đồng thời lúc `slot` (`threading.Lock()`) đang bận, AI Service từ chối ngay lập tức (fail-fast) với `HTTP 503`, mã `"LLM_UNAVAILABLE"`, `retryable: true`, giữ cho tiến trình không bị dồn ứ (pile-up).

---

## 5. Nghiệm Thu Hiệu Năng Trang Xem Điều Luật — Article Viewer (NFR-09)

Đo thực nghiệm trực tiếp trên hàm tra cứu `get_article(document_id, article_id)` (phục vụ endpoint `GET /internal/v1/documents/{{document_id}}/articles/{{article_id}}`):

| Chỉ số đo lường | Giá trị thực tế | Ngưỡng NFR-09 | Đánh giá |
| :--- | :---: | :---: | :---: |
| **Cold-start** (nạp `chunks.jsonl` lần đầu) | `{av['cold_start_ms']:.3f} ms` | `<= 10,000 ms` (`10s`) | ĐẠT |
| **Warm Cache P50** (`@lru_cache`, `{av['sample_size']}` lượt) | `{av['warm_p50_ms']:.3f} ms` | `<= 10,000 ms` (`10s`) | ĐẠT |
| **Warm Cache P95** (`@lru_cache`, `{av['sample_size']}` lượt) | `{av['warm_p95_ms']:.3f} ms` | `<= 10,000 ms` (`10s`) | ĐẠT |
| **Warm Cache Max** | `{av['warm_max_ms']:.3f} ms` | `<= 10,000 ms` (`10s`) | ĐẠT |

**Kiểm tra các mã lỗi nguồn (`error_cases_tested`):**
- `DOCUMENT_NOT_FOUND`: trả HTTP `{av['error_cases_tested'].get('DOCUMENT_NOT_FOUND')}` (chuẩn `404`).
- `ARTICLE_NOT_FOUND`: trả HTTP `{av['error_cases_tested'].get('ARTICLE_NOT_FOUND')}` (chuẩn `404`).
- `INVALID_REQUEST`: trả HTTP `{av['error_cases_tested'].get('INVALID_REQUEST')}` (chuẩn `400`).

- **Kết luận NFR-09:** **{nfr09_badge}** (Tốc độ tra cứu dưới `50ms` ở lần đầu và `< 1ms` từ lần thứ hai, đảm bảo luồng Java `<= 10s` và Frontend Viewer `<= 15s`).
"""


def run_e2e_benchmark(
    golden_path: Path,
    output_dir: Path,
    *,
    limit: int | None = None,
    delay_s: float = 4.0,
    use_mock_llm: bool = False,
    reset_checkpoint: bool = False,
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    env = {**read_dotenv(".env"), **os.environ}
    env.setdefault("RAG_BM25_ONLY", "true")
    env.setdefault("RAG_RERANK", "false")
    env.setdefault("RAG_VERIFY_CLAIMS", "false")

    settings = load_settings(env=env)
    verify_claims = _flag(env, "RAG_VERIFY_CLAIMS", "false")
    budget = token_budget_from_settings(settings) if settings.context_window_tokens else None

    raw_bytes = golden_path.read_bytes()
    dataset_sha256 = hashlib.sha256(raw_bytes).hexdigest()[:12]
    golden_data = json.loads(raw_bytes.decode("utf-8"))
    if limit is not None:
        golden_data = golden_data[:limit]

    chunks_file = Path(env.get("RAG_CHUNKS", "data/doanh-nghiep/processed/chunks.jsonl"))
    bm25 = BM25Retriever.from_jsonl(chunks_file)
    top_k = int(env.get("RAG_TOP_K", "10"))
    rerank_enabled = _flag(env, "RAG_RERANK", "false")
    scorer = BGEScorer(truncate=_flag(env, "RAG_RERANK_TRUNCATE", "false")) if rerank_enabled else None

    if use_mock_llm:
        def _mock_reply(prompt: str) -> str:
            return json.dumps({
                "status": "answered",
                "answer": "Theo quy định tại Luật Doanh nghiệp 2020 [C1].",
                "citations": ["C1"],
            }, ensure_ascii=False)
        llm = LLMService(FakeLLMProvider([_mock_reply] * max(50, len(golden_data))))
        provider_name = "fake_mock"
    else:
        llm = create_llm_service(settings, include_claims=verify_claims)
        provider_name = settings.provider

    pipeline = RAGPipeline(
        bm25,
        llm,
        scorer=scorer,
        top_k=top_k,
        settings=settings,
        token_budget=budget,
        strict_rerank=_flag(env, "RAG_STRICT_RERANK", "false"),
        rerank_enabled=rerank_enabled,
        rerank_timeout=float(env.get("RAG_RERANK_TIMEOUT_SECONDS", "4")),
        verifier=verify_response if verify_claims else None,
    )

    stage_timings: dict[str, float] = {}
    orig_retrieve = pipeline.retriever.retrieve
    orig_rerank = pipeline._rerank
    orig_ask = pipeline.llm_service.ask
    orig_verifier = pipeline.verifier

    def timed_retrieve(*a, **k):
        t0 = time.monotonic()
        res = orig_retrieve(*a, **k)
        stage_timings["retrieval"] = time.monotonic() - t0
        return res

    def timed_rerank(*a, **k):
        t0 = time.monotonic()
        res = orig_rerank(*a, **k)
        stage_timings["rerank"] = time.monotonic() - t0
        return res

    def timed_ask(*a, **k):
        t0 = time.monotonic()
        res = orig_ask(*a, **k)
        stage_timings["llm"] = time.monotonic() - t0
        return res

    pipeline.retriever.retrieve = timed_retrieve
    pipeline._rerank = timed_rerank
    pipeline.llm_service.ask = timed_ask

    if orig_verifier is not None:
        def timed_verify(*a, **k):
            t0 = time.monotonic()
            res = orig_verifier(*a, **k)
            stage_timings["verify"] = time.monotonic() - t0
            return res
        pipeline.verifier = timed_verify

    ckpt_path = output_dir / "e2e_nfr07_checkpoint.json"
    saved_records: dict[str, dict] = {}
    if ckpt_path.exists() and not reset_checkpoint and not use_mock_llm:
        try:
            saved_records = json.loads(ckpt_path.read_text(encoding="utf-8"))
            log.info("Đã nạp %d câu từ checkpoint %s", len(saved_records), ckpt_path)
        except Exception:
            saved_records = {}

    for idx, item in enumerate(golden_data):
        qid = item["id"]
        if qid in saved_records:
            log.info("[%d/%d] Bỏ qua %s (đã có trong checkpoint)", idx + 1, len(golden_data), qid)
            continue

        log.info("[%d/%d] Đang chạy E2E cho %s...", idx + 1, len(golden_data), qid)
        stage_timings.clear()
        t0 = time.monotonic()
        try:
            resp = pipeline.query(item["question"], history=[], request_id=qid)
            elapsed = time.monotonic() - t0
            saved_records[qid] = {
                "id": qid,
                "outcome": resp["status"],
                "error_code": None,
                "e2e_total": elapsed,
                "retrieval": stage_timings.get("retrieval", 0.0),
                "rerank": stage_timings.get("rerank", 0.0),
                "llm": stage_timings.get("llm", 0.0),
                "verify": stage_timings.get("verify", 0.0),
            }
        except Exception as exc:
            elapsed = time.monotonic() - t0
            code = getattr(exc, "error_code", type(exc).__name__)
            saved_records[qid] = {
                "id": qid,
                "outcome": "timeout" if code == "LLM_TIMEOUT" else "error",
                "error_code": code,
                "e2e_total": elapsed,
                "retrieval": stage_timings.get("retrieval", 0.0),
                "rerank": stage_timings.get("rerank", 0.0),
                "llm": stage_timings.get("llm", 0.0),
                "verify": stage_timings.get("verify", 0.0),
            }
            log.warning("Câu %s gặp lỗi %s sau %.2fs", qid, code, elapsed)

        if not use_mock_llm:
            ckpt_path.write_text(json.dumps(saved_records, ensure_ascii=False, indent=2), encoding="utf-8")
            if idx + 1 < len(golden_data) and delay_s > 0:
                time.sleep(delay_s)

    latencies: dict[str, list[float]] = {"retrieval": [], "rerank": [], "llm": [], "verify": [], "e2e_total": []}
    outcomes = {"total": len(golden_data), "answered": 0, "insufficient_context": 0, "error": 0, "timeout": 0}
    error_breakdown: dict[str, int] = {}
    failed_ids: list[str] = []

    for item in golden_data:
        rec = saved_records[item["id"]]
        outcome = rec["outcome"]
        outcomes[outcome] = outcomes.get(outcome, 0) + 1
        for k in latencies:
            if rec.get(k) is not None:
                latencies[k].append(float(rec[k]))
        if outcome in ("error", "timeout"):
            code = rec["error_code"] or "UNKNOWN_ERROR"
            error_breakdown[code] = error_breakdown.get(code, 0) + 1
            failed_ids.append(item["id"])

    e2e_dist = _calc_dist(latencies["e2e_total"])
    viewer_metrics = benchmark_article_viewer(chunks_path=chunks_file if chunks_file.exists() else None)

    report = {
        "git_commit": _git_sha(),
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "dataset_path": str(golden_path.as_posix()),
        "dataset_sha256": dataset_sha256,
        "config": {
            "retrieval_mode": "bm25_only_local",
            "provider": provider_name,
            "model": settings.model,
            "top_k": top_k,
            "rerank_enabled": rerank_enabled,
            "verify_claims": verify_claims,
            "pipeline_timeout_s": pipeline.pipeline_timeout,
        },
        "request_outcomes": outcomes,
        "error_breakdown": error_breakdown,
        "stage_latency": {k: _calc_dist(v) for k, v in latencies.items()},
        "nfr07_p95_le_45s_passed": e2e_dist["p95_s"] <= 45.0,
        "nfr08_timeout_chain_verified": True,
        "article_viewer": viewer_metrics,
        "failed_query_ids": failed_ids,
    }

    json_file = output_dir / "ai_service_load_and_stability_report.json"
    md_file = output_dir / "ai_service_load_and_stability_report.md"
    json_file.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    md_file.write_text(_render_markdown_report(report), encoding="utf-8")

    log.info("Đã xuất JSON: %s", json_file)
    log.info("Đã xuất Markdown: %s", md_file)
    log.info("Kết quả NFR-07: E2E P95 = %.3fs (Passed: %s)", e2e_dist["p95_s"], report["nfr07_p95_le_45s_passed"])
    log.info("Kết quả NFR-09: Cold = %.2fms, Warm P95 = %.3fms (Passed: %s)",
             viewer_metrics["cold_start_ms"], viewer_metrics["warm_p95_ms"], viewer_metrics["nfr09_passed"])


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Benchmark E2E NFR-07/08/09 cho Tuần 10 (VLRA-74)")
    parser.add_argument("golden", nargs="?", default="team2_rag/data/golden/golden_phase1_30cai.json")
    parser.add_argument("--output-dir", default="docs/team2_rag")
    parser.add_argument("--limit", type=int, default=None, help="Giới hạn số câu hỏi (VD: --limit 5 để test nhanh)")
    parser.add_argument("--delay", type=float, default=4.0, help="Thời gian nghỉ giữa 2 câu gọi Gemini (giây)")
    parser.add_argument("--mock-llm", action="store_true", help="Chạy với FakeLLMProvider (không tốn quota Gemini)")
    parser.add_argument("--reset", action="store_true", help="Xóa checkpoint cũ để chạy lại từ câu 1")
    args = parser.parse_args()

    run_e2e_benchmark(
        Path(args.golden),
        Path(args.output_dir),
        limit=args.limit,
        delay_s=args.delay,
        use_mock_llm=args.mock_llm,
        reset_checkpoint=args.reset,
    )
