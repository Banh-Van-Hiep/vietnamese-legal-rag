"""Đặc tả kiểu dữ liệu cho Verification Engine (VLRA-T2-24, Tuần 9).

Tuân thủ mục 4 trong team2_rag/docs_2/week9/tasks.md:
- Output nội bộ của LLM (LLMOutputV2, Claim)
- Kết quả kiểm định (ClaimCheck, CitationCheck, VerificationResult)
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class Claim(BaseModel):
    """Một mệnh đề/luận điểm pháp lý độc lập được phân rã từ câu trả lời."""
    claim_id: str = Field(..., description="Mã định danh claim, ví dụ: K1, K2...")
    text: str = Field(..., description="Nội dung khẳng định/luận điểm bằng tiếng Việt")
    citation_ids: List[str] = Field(
        default_factory=list,
        description="Danh sách mã trích dẫn chứng minh cho claim này, ví dụ: ['C1', 'C2']"
    )


class LLMOutputV2(BaseModel):
    """Schema output nội bộ của LLM phục vụ Verification, không lộ ra ngoài API."""
    status: str = Field(..., description="'answered' hoặc 'insufficient_context'")
    answer: str = Field(..., description="Câu trả lời hoàn chỉnh chứa marker [C1], [C2]...")
    citations: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Danh sách citation 9 trường theo citation-specification.md"
    )
    claims: List[Claim] = Field(
        default_factory=list,
        description="Danh sách các claim tách từ answer (rỗng nếu insufficient_context)"
    )


class ClaimCheck(BaseModel):
    """Kết quả kiểm tra tính xác thực ngữ nghĩa của một claim."""
    claim_id: str
    text: str
    supported: bool = Field(..., description="Claim có được chứng thực bởi context được trích dẫn hay không")
    verdict: str = Field(..., description="'SUPPORTED' | 'PARTIAL' | 'UNSUPPORTED' | 'CONTRADICTED'")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="Độ tin cậy của phán quyết")
    reason: str = Field(..., description="Lý do chi tiết cho phán quyết")
    cited_citations: List[str] = Field(default_factory=list)


class CitationCheck(BaseModel):
    """Kết quả kiểm tra tính hợp lệ về hình thức và metadata của một citation."""
    citation_id: str
    exists_in_context: bool = Field(..., description="Mã citation có nằm trong danh sách context chunk được cấp không")
    chunk_id_valid: bool = Field(..., description="chunk_id có khớp chính xác với chunk trong context không")
    metadata_valid: bool = Field(..., description="Thông tin Điều/Khoản/Điểm có khớp với nguồn không")
    supports_claim: bool = Field(..., description="Citation có được gán cho ít nhất một claim hợp lệ không")
    detail: Optional[str] = None


class VerificationResult(BaseModel):
    """Kết quả tổng thể của quá trình thẩm định 2 tầng."""
    passed: bool = Field(..., description="True nếu toàn bộ câu trả lời hợp lệ, không có hallucination hoặc bịa nguồn")
    claim_results: List[ClaimCheck] = Field(default_factory=list)
    citation_results: List[CitationCheck] = Field(default_factory=list)
    summary: Dict[str, Any] = Field(
        default_factory=dict,
        description="Thống kê tóm tắt: total_claims, supported_claims, hallucination_detected, correctness_score..."
    )
