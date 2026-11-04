"""Bộ tính toán chỉ số Benchmark định lượng cho Tuần 9 (VLRA-T2-25, VLRA-68).

Bao gồm 3 chỉ số cốt lõi:
1. Citation Correctness (Mục tiêu >= 90%):
   Tỷ lệ citation hợp lệ và thực sự hỗ trợ cho claim so với tổng số citation.
2. Citation Coverage (Mục tiêu >= 85%):
   Tỷ lệ các claim pháp lý được hỗ trợ bởi citation hợp lệ so với tổng số claim.
3. Hallucination Rate (Mục tiêu <= 5%):
   Tỷ lệ các câu trả lời bị phát hiện chứa thông tin ảo giác / ungrounded claims.
"""
from __future__ import annotations

from typing import Any, Dict, List
from team2_rag.verification.types import VerificationResult


def compute_benchmark_metrics(
    eval_results: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """Tính toán 3 chỉ số benchmark chính thức từ danh sách kết quả kiểm định các câu hỏi.

    Mỗi phần tử trong eval_results bao gồm:
    - query_id / case_id
    - status: 'answered' | 'insufficient_context' | 'error'
    - verification_result: VerificationResult (nếu answered)
    """
    total_queries = len(eval_results)
    answered_queries = 0
    insufficient_queries = 0
    error_queries = 0

    total_claims = 0
    supported_claims = 0

    total_citations = 0
    valid_citations = 0

    hallucinated_answers = 0

    for item in eval_results:
        status = item.get("status", "")
        if status == "insufficient_context":
            insufficient_queries += 1
            continue
        elif status != "answered":
            error_queries += 1
            continue

        answered_queries += 1
        v_res: VerificationResult = item.get("verification_result")
        if not v_res:
            continue

        sm = v_res.summary
        total_claims += sm.get("total_claims", 0)
        supported_claims += sm.get("supported_claims", 0)

        total_citations += sm.get("total_citations", 0)
        valid_citations += sm.get("valid_citations", 0)

        if sm.get("hallucination_detected", False) or not v_res.passed:
            hallucinated_answers += 1

    # Tính toán các tỷ lệ
    citation_correctness = (
        (valid_citations / total_citations) if total_citations > 0 else 1.0
    )
    citation_coverage = (
        (supported_claims / total_claims) if total_claims > 0 else 1.0
    )
    hallucination_rate = (
        (hallucinated_answers / answered_queries) if answered_queries > 0 else 0.0
    )

    metrics = {
        "dataset_summary": {
            "total_queries": total_queries,
            "answered_queries": answered_queries,
            "insufficient_context_queries": insufficient_queries,
            "error_queries": error_queries,
        },
        "claims_summary": {
            "total_claims": total_claims,
            "supported_claims": supported_claims,
            "unsupported_claims": total_claims - supported_claims,
        },
        "citations_summary": {
            "total_citations": total_citations,
            "valid_citations": valid_citations,
            "invalid_citations": total_citations - valid_citations,
        },
        "core_metrics": {
            "citation_correctness": round(citation_correctness, 4),
            "citation_correctness_pct": f"{citation_correctness * 100:.2f}%",
            "citation_coverage": round(citation_coverage, 4),
            "citation_coverage_pct": f"{citation_coverage * 100:.2f}%",
            "hallucination_rate": round(hallucination_rate, 4),
            "hallucination_rate_pct": f"{hallucination_rate * 100:.2f}%",
        },
        "targets_check": {
            "citation_correctness_target_met": citation_correctness >= 0.90,
            "citation_coverage_target_met": citation_coverage >= 0.85,
            "hallucination_rate_target_met": hallucination_rate <= 0.05,
        }
    }

    return metrics
