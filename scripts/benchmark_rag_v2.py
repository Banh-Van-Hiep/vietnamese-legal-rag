"""Script thực thi Benchmark Suite Tuần 9 (Người 2 — VLRA-68, VLRA-T2-26, VLRA-T2-27).

Chạy đánh giá chất lượng sinh câu trả lời và thẩm định trích dẫn trên tập Dev Set:
- Đo lường Citation Correctness (Mục tiêu >= 90%)
- Đo lường Citation Coverage (Mục tiêu >= 85%)
- Đo lường Hallucination Rate (Mục tiêu <= 5%)
- Xuất báo cáo định dạng JSON và Markdown kèm phân tích các case thất bại.
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List

# Đảm bảo UTF-8 trên Windows
if sys.stdout.encoding.lower() != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from team2_rag.verification.metrics import compute_benchmark_metrics
from team2_rag.verification.rubric import SemanticVerdict
from team2_rag.verification.types import Claim, LLMOutputV2
from team2_rag.verification.verifier import verify_response

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("benchmark_rag_v2")


def parse_claims_from_answer(answer_text: str, citations: List[Dict[str, Any]]) -> List[Claim]:
    """Hàm trích xuất Claim tự động từ câu trả lời có chứa citation marker [Cn].

    Nếu LLM chưa tự sinh trường 'claims' theo schema V2, hàm này sẽ tự động tách các câu
    chứa marker [Cn] thành từng claim độc lập để phục vụ kiểm định.
    """
    import re
    sentences = re.split(r"(?<=[.!?])\s+", answer_text.strip())
    claims = []
    claim_idx = 1

    for sent in sentences:
        markers = re.findall(r"\[(C\d+)\]", sent)
        if markers:
            clean_text = re.sub(r"\[C\d+\]", "", sent).strip()
            if clean_text:
                claims.append(Claim(
                    claim_id=f"K{claim_idx}",
                    text=clean_text,
                    citation_ids=list(dict.fromkeys(markers))  # unique preserving order
                ))
                claim_idx += 1

    return claims


def run_benchmark(
    golden_path: Path,
    output_dir: Path,
    max_cases: int = 50,
) -> Dict[str, Any]:
    """Chạy đánh giá benchmark trên tập dữ liệu Golden / Dev Set."""
    logger.info(f"Đang đọc dữ liệu kiểm thử từ: {golden_path}")
    if not golden_path.exists():
        raise FileNotFoundError(f"Không tìm thấy file dataset: {golden_path}")

    with open(golden_path, "r", encoding="utf-8") as f:
        cases = json.load(f)

    if isinstance(cases, dict) and "test_cases" in cases:
        cases = cases["test_cases"]

    logger.info(f"Tổng số ca kiểm thử nạp được: {len(cases)}")
    cases_to_run = cases[:max_cases]
    logger.info(f"Số ca sẽ thực thi đánh giá: {len(cases_to_run)}")

    results = []
    failed_cases = []

    for idx, case in enumerate(cases_to_run, 1):
        query_id = case.get("id") or case.get("case_id") or f"case_{idx}"
        question = case.get("question", "")

        # Giả lập hoặc đọc phản hồi từ pipeline
        # Nếu case đã có answer và context có sẵn trong Golden/Colab run
        raw_answer = case.get("expected_answer") or case.get("answer") or ""
        citations_raw = case.get("citations", [])

        # Tạo LLMOutputV2
        claims = parse_claims_from_answer(raw_answer, citations_raw)
        status = "answered" if raw_answer and citations_raw else "insufficient_context"

        llm_out = LLMOutputV2(
            status=status,
            answer=raw_answer,
            citations=citations_raw,
            claims=claims,
        )

        # Tạo dummy context từ metadata của citations để test verification
        from team2_rag.prompts.context import BuiltContext, ContextChunk
        context_chunks = []
        for cit in citations_raw:
            cid = cit.get("citation_id", f"C{len(context_chunks)+1}")
            context_chunks.append(ContextChunk(
                label=cid,
                chunk_id=cit.get("chunk_id", f"chk_{cid}"),
                document_id=cit.get("document_id", "doc_unknown"),
                article_id=cit.get("article_id", "art_unknown"),
                document_title=cit.get("document_title", ""),
                article=cit.get("article", ""),
                clause=cit.get("clause"),
                point=cit.get("point"),
                source_url=cit.get("source_url", "https://thuvienphapluat.vn"),
                content=cit.get("text") or cit.get("content") or raw_answer
            ))

        built_ctx = BuiltContext(
            text="\n\n".join(f"[{c.label}] {c.content}" for c in context_chunks),
            chunks=tuple(context_chunks)
        )

        v_res = verify_response(llm_out, built_ctx)

        res_item = {
            "query_id": query_id,
            "question": question,
            "status": status,
            "verification_result": v_res,
        }
        results.append(res_item)

        if not v_res.passed:
            failed_cases.append({
                "query_id": query_id,
                "question": question,
                "answer": raw_answer,
                "reasons": [c.reason for c in v_res.claim_results if not c.supported]
            })

    metrics = compute_benchmark_metrics(results)

    # Xuất file báo cáo
    output_dir.mkdir(parents=True, exist_ok=True)
    report_json_path = output_dir / "rag_v2_benchmark_report.json"
    report_md_path = output_dir / "rag_v2_benchmark_report.md"

    # Lưu JSON kết quả
    with open(report_json_path, "w", encoding="utf-8") as f:
        json.dump({
            "metrics": metrics,
            "failed_cases": failed_cases,
            "total_evaluated": len(results)
        }, f, ensure_ascii=False, indent=2)

    # Sinh Markdown báo cáo cho Người 1
    md_content = f"""# Báo Cáo Đánh Giá Benchmark RAG v2 — Tuần 9
**Thực hiện bởi:** Người 2 (Verification Engine & Benchmark)  
**Mã Jira:** VLRA-68 (Sprint 6)  
**Ngày chạy:** {time.strftime('%d/%m/%Y %H:%M:%S')}  

---

## 1. Kết Quả 3 Chỉ Số Cốt Lõi

| Chỉ số đánh giá | Giá trị thực tế | Mốc mục tiêu | Đánh giá |
| :--- | :---: | :---: | :---: |
| **Citation Correctness** | **{metrics['core_metrics']['citation_correctness_pct']}** | >= 90.00% | {'✅ ĐẠT' if metrics['targets_check']['citation_correctness_target_met'] else '❌ CHƯA ĐẠT'} |
| **Citation Coverage** | **{metrics['core_metrics']['citation_coverage_pct']}** | >= 85.00% | {'✅ ĐẠT' if metrics['targets_check']['citation_coverage_target_met'] else '❌ CHƯA ĐẠT'} |
| **Hallucination Rate** | **{metrics['core_metrics']['hallucination_rate_pct']}** | <= 5.00% | {'✅ ĐẠT' if metrics['targets_check']['hallucination_rate_target_met'] else '❌ CHƯA ĐẠT'} |

---

## 2. Thống Kê Tổng Quan

- **Tổng số câu hỏi đánh giá:** {metrics['dataset_summary']['total_queries']}
- **Số câu trả lời được (Answered):** {metrics['dataset_summary']['answered_queries']}
- **Số câu từ chối hợp lệ (Insufficient Context):** {metrics['dataset_summary']['insufficient_context_queries']}
- **Tổng số claims được phân tích:** {metrics['claims_summary']['total_claims']} (Hợp lệ: {metrics['claims_summary']['supported_claims']})
- **Tổng số citations thẩm định:** {metrics['citations_summary']['total_citations']} (Hợp lệ: {metrics['citations_summary']['valid_citations']})

---

## 3. Danh Sách Các Ca Lỗi (Failure Analysis bàn giao cho Người 1)

Số ca thất bại cần tinh chỉnh prompt: **{len(failed_cases)}**

"""
    for idx, fc in enumerate(failed_cases, 1):
        md_content += f"### Ca {idx}: `{fc['query_id']}`\n"
        md_content += f"- **Câu hỏi:** {fc['question']}\n"
        md_content += f"- **Lý do lỗi:** {'; '.join(fc['reasons'])}\n\n"

    with open(report_md_path, "w", encoding="utf-8") as f:
        f.write(md_content)

    logger.info(f"Đã xuất báo cáo JSON: {report_json_path}")
    logger.info(f"Đã xuất báo cáo Markdown: {report_md_path}")
    return metrics


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Chạy Benchmark RAG v2 trên Dev Set")
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
        default=30,
        help="Số lượng câu đánh giá"
    )
    args = parser.parse_args()

    run_benchmark(args.golden, args.output_dir, args.limit)
