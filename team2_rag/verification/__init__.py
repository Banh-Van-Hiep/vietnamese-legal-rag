"""Module Verification Engine & Benchmark cho Team 2 (Tuần 9 — VLRA-67, VLRA-68).

Cung cấp:
- Schema output nội bộ có claims: Claim, LLMOutputV2
- Kết quả kiểm định: ClaimCheck, CitationCheck, VerificationResult
- Hàm thẩm định: verify_response(output, context)
- Thước đo chất lượng: calculate_metrics(results)
"""
from team2_rag.verification.rubric import RubricScore, SemanticVerdict
from team2_rag.verification.types import (
    CitationCheck,
    Claim,
    ClaimCheck,
    LLMOutputV2,
    VerificationResult,
)
from team2_rag.verification.verifier import CitationVerifier, verify_response

__all__ = [
    "Claim",
    "LLMOutputV2",
    "ClaimCheck",
    "CitationCheck",
    "VerificationResult",
    "RubricScore",
    "SemanticVerdict",
    "CitationVerifier",
    "verify_response",
]
