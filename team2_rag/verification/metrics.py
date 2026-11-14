"""Bộ tính toán chỉ số Benchmark định lượng cho Tuần 9 (VLRA-T2-25, VLRA-68).

Bao gồm 3 chỉ số cốt lõi:
1. Citation Correctness (Mục tiêu >= 90%):
   Tỷ lệ citation hợp lệ và thực sự hỗ trợ cho claim so với tổng số citation.
   Nếu không có citation nào (0 citation), trả về None ("chưa đo"), không mặc định 100%.

2. Citation Coverage (Mục tiêu >= 85%):
   Tỷ lệ các claim pháp lý được hỗ trợ bởi citation hợp lệ so với tổng số claim.
   Nếu không có claim nào (0 claim), trả về None ("chưa đo"), không mặc định 100%.

3. Hallucination Rate (Mục tiêu <= 5%):
   Thống nhất đo lường ở 2 cấp độ:
   - Query-level Hallucination Rate: Tỷ lệ câu trả lời chứa ít nhất một claim bị ảo giác / tổng số câu answered.
   - Claim-level Hallucination Rate: Tỷ lệ nhận định pháp lý không có căn cứ / tổng số claim.
   Nếu không có câu answered nào, trả về None ("chưa đo").
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional
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
        v_res: Optional[VerificationResult] = item.get("verification_result")
        if not v_res:
            continue

        sm = v_res.summary
        total_claims += sm.get("total_claims", 0)
        supported_claims += sm.get("supported_claims", 0)

        total_citations += sm.get("total_citations", 0)
        valid_citations += sm.get("valid_citations", 0)

        if sm.get("hallucination_detected", False) or not v_res.passed:
            hallucinated_answers += 1

    # Tính toán các tỷ lệ: Không gán mặc định điểm tuyệt đối khi không có mẫu đo
    citation_correctness: Optional[float] = (
        round(valid_citations / total_citations, 4) if total_citations > 0 else None
    )
    citation_coverage: Optional[float] = (
        round(supported_claims / total_claims, 4) if total_claims > 0 else None
    )
    query_hallucination_rate: Optional[float] = (
        round(hallucinated_answers / answered_queries, 4) if answered_queries > 0 else None
    )
    claim_hallucination_rate: Optional[float] = (
        round((total_claims - supported_claims) / total_claims, 4) if total_claims > 0 else None
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
            "citation_correctness": citation_correctness,
            "citation_correctness_pct": f"{citation_correctness * 100:.2f}%" if citation_correctness is not None else "chưa đo (0 citation)",
            "citation_coverage": citation_coverage,
            "citation_coverage_pct": f"{citation_coverage * 100:.2f}%" if citation_coverage is not None else "chưa đo (0 claim)",
            "query_hallucination_rate": query_hallucination_rate,
            "query_hallucination_rate_pct": f"{query_hallucination_rate * 100:.2f}%" if query_hallucination_rate is not None else "chưa đo (0 câu answered)",
            "claim_hallucination_rate": claim_hallucination_rate,
            "claim_hallucination_rate_pct": f"{claim_hallucination_rate * 100:.2f}%" if claim_hallucination_rate is not None else "chưa đo (0 claim)",
            # Giữ trường cũ để tương thích với các script hiện tại
            "hallucination_rate": query_hallucination_rate,
            "hallucination_rate_pct": f"{query_hallucination_rate * 100:.2f}%" if query_hallucination_rate is not None else "chưa đo (0 câu answered)",
        },
        "targets_check": {
            "citation_correctness_target_met": (citation_correctness >= 0.90) if citation_correctness is not None else False,
            "citation_coverage_target_met": (citation_coverage >= 0.85) if citation_coverage is not None else False,
            "hallucination_rate_target_met": (query_hallucination_rate <= 0.05) if query_hallucination_rate is not None else False,
        }
    }

    return metrics
