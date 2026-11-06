"""Runner thực thi Benchmark Suite Tuần 9 (Người 2 — VLRA-68, VLRA-T2-26, VLRA-T2-27).

Đặc điểm kỹ thuật:
- Tái sử dụng RAGPipeline v2 thật (Retrieval -> Reranker -> LLM -> Verification).
- Bật `include_claims=True` trên LLMService để LLM tự khai nhận định và trích dẫn.
- Có cơ chế Checkpoint & Resume từng câu: chống gián đoạn, không phải chạy lại từ đầu khi gặp sự cố mạng.
- Tự động throttle (nghỉ ngắn giữa các câu) chống quá tải Rate Limit trên Google API.
- Báo cáo chuẩn T2-26: ghi rõ Commit SHA, Config (trọng số, top_k, rerank), SHA-256 Golden, nhãn exploratory.
- Phân loại ca lỗi T2-27 thành 4 nhóm: nguồn sai, claim không nguồn, prompt, retrieval.
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
from pathlib import Path
from typing import Any, Dict, List, Optional

# Đảm bảo UTF-8 trên Windows
if sys.stdout.encoding.lower() != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

import dotenv
dotenv.load_dotenv(".env")

from team2_rag.config.settings import load_settings
from team2_rag.llm.errors import CitationInvalidError, LLMBadOutputError, LLMContentBlockedError, LLMError
from team2_rag.runtime import build_runtime
from team2_rag.verification.metrics import compute_benchmark_metrics
from team2_rag.verification.types import Claim, LLMOutputV2, VerificationResult
from team2_rag.verification.verifier import verify_response

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("benchmark_rag_v2")


def get_git_commit_sha() -> str:
    """Lấy SHA commit git hiện tại."""
    try:
        out = subprocess.check_output(["git", "rev-parse", "HEAD"], stderr=subprocess.DEVNULL)
        return out.decode("utf-8").strip()
    except Exception:
        return "unknown"


def compute_file_sha256(path: Path) -> str:
    """Tính mã băm SHA-256 của file dữ liệu (chuẩn hóa LF để nhất quán trên mọi OS/Git)."""
    with open(path, "rb") as f:
        content = f.read()
    normalized = content.replace(b"\r\n", b"\n")
    return hashlib.sha256(normalized).hexdigest()


def classify_failure(
    case: Dict[str, Any],
    v_res: Optional[VerificationResult],
    status: str,
    retrieved_chunk_ids: List[str],
    error: Optional[BaseException] = None,
) -> str:
    """Phân loại nguyên nhân thất bại chuẩn xác theo T2-27:

    - 'timeout / hạ tầng': Quá hạn phản hồi LLM hoặc mạng/dịch vụ
    - 'hạ tầng (503/504)': Lỗi upstream từ provider
    - 'prompt': Định dạng sai, JSON malformed, thiếu marker do prompt
    - 'nguồn sai': Citation trích dẫn không khớp hoặc bịa metadata
    - 'claim không có nguồn': Claim bị đánh giá UNSUPPORTED/CONTRADICTED (Hallucination)
    - 'retrieval': Không tìm thấy ngữ cảnh phù hợp
    """
    if error is not None:
        # Lỗi ngoại lệ phân theo loại: timeout hay quá tải LLM không phải lỗi prompt, người sửa prompt không xử lý được.
        if isinstance(error, CitationInvalidError):
            return "nguồn sai (Verification không qua)"
        if isinstance(error, (LLMBadOutputError, LLMContentBlockedError)):
            return "prompt (LLM trả sai form hoặc bị chặn nội dung)"
        if isinstance(error, LLMError):
            return "hạ tầng LLM (timeout, quá tải hoặc cấu hình; không phải lỗi prompt)"
        return "hệ thống (lỗi ngoài LLM, xem log)"
    if status == "error":
        return "hệ thống (trạng thái error)"

    if status == "insufficient_context":
        return "retrieval (hệ thống từ chối do không đủ ngữ cảnh)"

    if not v_res:
        return "prompt (không sinh được cấu trúc phản hồi hợp lệ)"

    # Kiểm tra metadata và provenance
    has_cit_error = any(
        not (c.exists_in_context and c.chunk_id_valid and c.metadata_valid)
        for c in v_res.citation_results
    )
    if has_cit_error:
        return "nguồn sai (citation trỏ nhầm hoặc sai metadata)"

    # Kiểm tra claims không có nguồn
    unsupported_claims = [c for c in v_res.claim_results if not c.supported]
    if unsupported_claims:
        return "claim không có nguồn (nội dung khẳng định không có trong điều luật)"

    return "prompt (không vượt qua bộ kiểm định cú pháp/marker)"


def run_pipeline_benchmark(
    golden_path: Path,
    output_dir: Path,
    max_cases: int = 50,
    throttle_seconds: float = 1.5,
    checkpoint_file: Optional[Path] = None,
) -> Dict[str, Any]:
    """Chạy đánh giá benchmark trên tập dữ liệu Golden / Dev Set bằng Pipeline thật."""
    logger.info(f"Khởi động Benchmark Runner trên tập dữ liệu: {golden_path}")
    if not golden_path.exists():
        raise FileNotFoundError(f"Không tìm thấy file Golden: {golden_path}")

    golden_sha256 = compute_file_sha256(golden_path)
    git_commit = get_git_commit_sha()

    with open(golden_path, "r", encoding="utf-8") as f:
        cases = json.load(f)

    if isinstance(cases, dict) and "test_cases" in cases:
        cases = cases["test_cases"]

    cases_to_run = cases[:max_cases]
    logger.info(f"Tổng số ca nạp: {len(cases)} — Sẽ thực thi: {len(cases_to_run)} ca")

    # Quản lý Checkpoint
    checkpoint_path = checkpoint_file or (output_dir / "benchmark_checkpoint.json")
    checkpoint_data: Dict[str, Any] = {}
    if checkpoint_path.exists():
        try:
            with open(checkpoint_path, "r", encoding="utf-8") as f:
                checkpoint_data = json.load(f)
            logger.info(f"Nạp lại checkpoint thành công: đã có {len(checkpoint_data)} ca hoàn tất.")
        except Exception as e:
            logger.warning(f"Không thể đọc checkpoint ({e}), chạy mới từ đầu.")

# Khởi tạo Runtime với pipeline thật
    logger.info("Đang khởi tạo RAG Runtime (tắt fallback model để đo đạc trung thực)...")
    os.environ["LLM_ALLOW_FALLBACK"] = "false"
    rt = build_runtime()
    pipeline = rt.pipeline
    # Bật chế độ include_claims để prompt ép LLM khai claims
    pipeline.llm_service.include_claims = True
    if hasattr(pipeline.llm_service.provider, "allow_fallback"):
        pipeline.llm_service.provider.allow_fallback = False

    # Cấu hình hiện tại để đưa vào báo cáo
    cfg_report = {
        "git_commit": git_commit,
        "golden_dataset": str(golden_path),
        "golden_sha256": golden_sha256,
        "dataset_status": "exploratory (Dev Set chưa đóng băng hoàn toàn)",
        "llm_model": getattr(pipeline.llm_service.provider, "model", "unknown"),
        "allow_fallback": False,
        "pipeline_timeout": getattr(pipeline, "pipeline_timeout", 45.0),
        "top_k": pipeline.top_k,
        "rerank_enabled": pipeline.rerank_enabled,
        "strict_rerank": pipeline.strict_rerank,
        "rerank_timeout": pipeline.rerank_timeout,
        "rerank_note": "Tắt rerank (không chạy BGE-Reranker)" if not pipeline.rerank_enabled else "Bật BGE-Reranker-v2-m3",
        "weights": getattr(pipeline.retriever, "weights", "(0.5, 1.0)"),
    }

    eval_results = []
    failed_cases = []

    try:
        for idx, case in enumerate(cases_to_run, 1):
            query_id = str(case.get("id") or case.get("case_id") or f"case_{idx}")
            question = case.get("question", "").strip()

            # Kiểm tra checkpoint
            if query_id in checkpoint_data:
                logger.info(f"[{idx}/{len(cases_to_run)}] Bỏ qua '{query_id}' (đã có trong checkpoint)")
                saved_res = checkpoint_data[query_id]
                # Reconstruct VerificationResult nếu có
                v_res = None
                if saved_res.get("verification_result"):
                    v_res = VerificationResult.model_validate(saved_res["verification_result"])
                eval_results.append({
                    "query_id": query_id,
                    "question": question,
                    "status": saved_res.get("status"),
                    "verification_result": v_res,
                })
                if not saved_res.get("passed", True):
                    failed_cases.append(saved_res.get("failure_info"))
                continue

            logger.info(f"[{idx}/{len(cases_to_run)}] Đang chạy câu hỏi: '{query_id}'...")
            t_start = time.time()
            v_res = None
            last_exc = None
            status = "error"
            answer_text = ""
            citations_res = []
            claims_res = []
            failure_info = None
            error = None

            try:
                # 1. Chạy qua retrieval & rerank
                retrieved = pipeline.retriever.retrieve(question, top_k=pipeline.top_k)
                details = pipeline._rerank(retrieved)
                results_candidates = details.output.get("results", [])

                if not results_candidates:
                    status = "insufficient_context"
                    answer_text = "Không có ứng viên phù hợp từ retrieval."
                else:
                    # 2. Sinh câu trả lời có claims
                    from team2_rag.answer import generate_answer_detailed
                    generated = generate_answer_detailed(
                        details.output, [], llm_service=pipeline.llm_service,
                        settings=pipeline.settings, token_budget=pipeline.token_budget,
                    )
                    resp = generated.response
                    status = resp.get("status", "answered")
                    answer_text = resp.get("answer", "")
                    citations_res = resp.get("citations", [])

                    # 3. Chạy Verification thật của Người 2
                    if status == "answered":
                        output_v2 = LLMOutputV2(
                            status=status,
                            answer=answer_text,
                            citations=citations_res,
                            claims=[Claim(claim_id=c.claim_id, text=c.text, citation_ids=list(c.citation_ids))
                                    for c in generated.claims]
                        )
                        v_res = verify_response(output_v2, generated.context)
                        claims_res = [c.model_dump() for c in output_v2.claims]

            except Exception as exc:
                last_exc = exc
                logger.error(f"Lỗi khi xử lý câu '{query_id}': {exc}")
                status = "error"
                error = exc
                answer_text = f"Exception: {type(exc).__name__}: {exc}"

            actual_model = getattr(pipeline.llm_service.provider, "actual_model", getattr(pipeline.llm_service.provider, "model", "unknown"))

            is_passed = (v_res.passed if v_res else (status == "insufficient_context"))

            if not is_passed or status == "error":
                fail_cat = classify_failure(case, v_res, status, [c.get("chunk_id", "") for c in citations_res], error)
                reasons = []
                if v_res:
                    reasons = [c.reason for c in v_res.claim_results if not c.supported]
                    reasons += [f"{c.citation_id}: {c.detail}" for c in v_res.citation_results if not c.exists_in_context or not c.chunk_id_valid or not c.metadata_valid]
                if not reasons:
                    reasons = [f"Trạng thái: {status}"]

                failure_info = {
                    "query_id": query_id,
                    "question": question,
                    "status": status,
                    "failure_category": fail_cat,
                    "answer": answer_text[:300],
                    "reasons": reasons,
                }
                failed_cases.append(failure_info)

            # Lưu vào checkpoint
            checkpoint_data[query_id] = {
                "query_id": query_id,
                "question": question,
                "status": status,
                "actual_model": actual_model,
                "passed": is_passed,
                "elapsed_seconds": round(time.time() - t_start, 2),
                "answer": answer_text,
                "citations_count": len(citations_res),
                "claims_count": len(claims_res),
                "verification_result": v_res.model_dump() if v_res else None,
                "failure_info": failure_info,
            }
            with open(checkpoint_path, "w", encoding="utf-8") as f:
                json.dump(checkpoint_data, f, ensure_ascii=False, indent=2)

            eval_results.append({
                "query_id": query_id,
                "question": question,
                "status": status,
                "verification_result": v_res,
            })

            # Throttle tránh nghẽn API
            if throttle_seconds > 0:
                time.sleep(throttle_seconds)

    finally:
        rt.close()

    # Tính toán bộ metrics
    metrics = compute_benchmark_metrics(eval_results)

    # Thống kê phân loại lỗi
    cat_counts: Dict[str, int] = {}
    for fc in failed_cases:
        cat = fc.get("failure_category", "khác")
        cat_counts[cat] = cat_counts.get(cat, 0) + 1

    # Xuất báo cáo JSON
    output_dir.mkdir(parents=True, exist_ok=True)
    report_json_path = output_dir / "rag_v2_benchmark_report.json"
    report_md_path = output_dir / "rag_v2_benchmark_report.md"

    final_report = {
        "metadata": cfg_report,
        "metrics": metrics,
        "failure_analysis": {
            "total_failed": len(failed_cases),
            "categories": cat_counts,
            "failed_cases": failed_cases,
        },
        "raw_results": list(checkpoint_data.values()),
        "raw_results_count": len(eval_results),
    }

    with open(report_json_path, "w", encoding="utf-8") as f:
        json.dump(final_report, f, ensure_ascii=False, indent=2)

    # Sinh Markdown báo cáo bàn giao chuẩn cho Người 1 (Đạt)
    c_met = metrics["core_metrics"]
    t_check = metrics["targets_check"]
    d_sum = metrics["dataset_summary"]

    md_content = f"""# Báo Cáo Đánh Giá Benchmark RAG v2 — Tuần 9 (VLRA-T2-26, VLRA-68)
**Thực hiện bởi:** Người 2 (Verification Engine & Benchmark Suite)  
**Người nhận bàn giao:** Người 1 (Đạt — Core Pipeline & Prompting)  
**Thời điểm thực thi:** {time.strftime('%d/%m/%Y %H:%M:%S')}  
**Nhãn đánh giá:** `EXPLORATORY` *(Do tập Dev Set 70/110 câu của Team 1 chưa đóng băng)*  

---

## 1. Thông Tin Môi Trường & Cấu Hình Thử Nghiệm

| Thông số cấu hình | Giá trị thiết lập | Ghi chú |
| :--- | :--- | :--- |
| **Git Commit SHA** | `{git_commit[:10]}` | Nhánh `feature/team2-rag` |
| **Tập dữ liệu Golden** | `{cfg_report['golden_dataset']}` | Hash SHA-256: `{golden_sha256[:12]}...` |
| **Mô hình LLM Benchmark** | `{cfg_report['llm_model']}` | Chạy thật qua Google API v1beta |
| **Trạng thái Fallback Model** | `TẮT (LLM_ALLOW_FALLBACK=false)` | Bảo đảm 100% câu hỏi do đúng model cấu hình xử lý |
| **Ngân sách thời gian Pipeline** | `{cfg_report.get('pipeline_timeout', 45.0)}s` trần toàn luồng | Cưỡng chế trần NFR-07 (LLM <= 30s, Retrieval <= 10s, Rerank <= 4s) |
| **Tham số Retrieval** | `RAG_TOP_K={cfg_report['top_k']}`, `weights={cfg_report['weights']}` | BM25 + Qdrant Dense |
| **Cấu hình Reranker** | `enabled={cfg_report['rerank_enabled']}`, `timeout={cfg_report['rerank_timeout']}s` | {cfg_report.get('rerank_note', 'BGE-Reranker-v2-m3')} |
| **Cơ chế Claims & Verifier** | `include_claims=True`, `verifier=verify_response` | Kích hoạt bộ kiểm định 2 tầng Người 2 |

---

## 2. Kết Quả 3 Chỉ Số Cốt Lõi

| Chỉ số đánh giá | Giá trị thực tế | Mốc mục tiêu | Đánh giá |
| :--- | :---: | :---: | :---: |
| **Citation Correctness** | **{c_met['citation_correctness_pct']}** | >= 90.00% | {'✅ ĐẠT' if t_check['citation_correctness_target_met'] else '❌ CHƯA ĐẠT'} |
| **Citation Coverage** | **{c_met['citation_coverage_pct']}** | >= 85.00% | {'✅ ĐẠT' if t_check['citation_coverage_target_met'] else '❌ CHƯA ĐẠT'} |
| **Query-level Hallucination Rate** | **{c_met['query_hallucination_rate_pct']}** | <= 5.00% | {'✅ ĐẠT' if t_check['hallucination_rate_target_met'] else '❌ CHƯA ĐẠT'} |
| **Claim-level Hallucination Rate** | **{c_met['claim_hallucination_rate_pct']}** | Tham chiếu | Bổ sung theo yêu cầu Người 1 |

*Ghi chú:* Các trường hợp không có mẫu số (0 citation / 0 claim / 0 answered) được ghi rõ `"chưa đo"`, tuyệt đối không tính 100% giả định.

---

## 3. Thống Kê Tổng Quan Theo Nhóm Câu

- **Tổng số câu hỏi đánh giá:** {d_sum['total_queries']}
- **Số câu trả lời được (Answered):** {d_sum['answered_queries']}
- **Số câu hệ thống từ chối (Insufficient Context):** {d_sum['insufficient_context_queries']}
- **Số câu gặp lỗi kỹ thuật (Error):** {d_sum['error_queries']}
- **Tổng số nhận định (Claims) phân tích:** {metrics['claims_summary']['total_claims']} (Hợp lệ: {metrics['claims_summary']['supported_claims']}, Nghi vấn: {metrics['claims_summary']['unsupported_claims']})
- **Tổng số trích dẫn (Citations) thẩm định:** {metrics['citations_summary']['total_citations']} (Hợp lệ: {metrics['citations_summary']['valid_citations']}, Bất thường: {metrics['citations_summary']['invalid_citations']})

---

## 4. Phân Tích Ca Thất Bại Bàn Giao Cho Người 1 (VLRA-T2-27)

Tổng số ca thất bại / cần tinh chỉnh: **{len(failed_cases)}**

### Phân loại nguyên nhân lỗi:
"""
    for cat, count in cat_counts.items():
        md_content += f"- **{cat.capitalize()}**: {count} ca\n"

    md_content += "\n### Chi tiết từng ca lỗi:\n"
    for idx, fc in enumerate(failed_cases, 1):
        md_content += f"#### Ca {idx}: `{fc['query_id']}`\n"
        md_content += f"- **Câu hỏi:** {fc['question']}\n"
        md_content += f"- **Nhóm lỗi:** `{fc['failure_category']}`\n"
        md_content += f"- **Lý do chi tiết:** {'; '.join(fc['reasons'])}\n"
        md_content += f"- **Trích xuất câu trả lời:** _{fc['answer']}_\n\n"

    with open(report_md_path, "w", encoding="utf-8") as f:
        f.write(md_content)

    logger.info(f"Đã xuất báo cáo JSON: {report_json_path}")
    logger.info(f"Đã xuất báo cáo Markdown: {report_md_path}")
    return final_report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Chạy Benchmark RAG v2 trên Dev Set bằng Pipeline thật")
    parser.add_argument(
        "--golden",
        type=Path,
        default=Path("team2_rag/data/golden/golden_phase1_30cai.json"),
        help="Đường dẫn tới file Golden Dataset"
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("docs/team2_rag"),
        help="Thư mục lưu báo cáo"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=10,
        help="Số lượng câu đánh giá"
    )
    parser.add_argument(
        "--throttle",
        type=float,
        default=1.5,
        help="Thời gian nghỉ (giây) giữa các câu để chống nghẽn API"
    )
    args = parser.parse_args()

    run_pipeline_benchmark(args.golden, args.output_dir, args.limit, args.throttle)
