"""Bộ máy thẩm định trích dẫn 2 tầng (Citation Verification Engine — VLRA-T2-24).

Thiết kế kiến trúc 2 tầng:
- TẦNG 1: FORMAL & PROVENANCE VERIFICATION
  + Kiểm tra mã nhãn [Cn] và đối chiếu với tập Context Chunk hợp lệ trong lượt truy vấn.
  + Thẩm định tính toàn vẹn của 9 trường metadata (document_id, article_id, Điều, Khoản...).
  + Phát hiện trích dẫn bịa hoặc trỏ sai nguồn.
- TẦNG 2: SEMANTIC CLAIM-CITATION VERIFICATION
  + Phân tích từng nhận định (Claim) đối chiếu với nội dung đoạn văn bản luật được viện dẫn.
  + Chấm điểm Entailment/Faithfulness theo Rubric pháp lý Việt Nam.
  + Phát hiện thông tin ảo giác (Hallucination) hoặc suy diễn ngoài ngữ cảnh.
"""
from __future__ import annotations

import logging
from typing import Dict, List, Optional

from team2_rag.prompts.context import BuiltContext, ContextChunk
from team2_rag.verification.rubric import (
    SemanticVerdict,
    evaluate_claim_against_chunk,
)
from team2_rag.verification.types import (
    CitationCheck,
    ClaimCheck,
    LLMOutputV2,
    VerificationResult,
)

logger = logging.getLogger("team2_rag.verification")
logger.addHandler(logging.NullHandler())


class CitationVerifier:
    """Class thẩm định trích dẫn và phát hiện hallucination cho RAG Pipeline v2."""

    def __init__(self, strict_mode: bool = True):
        self.strict_mode = strict_mode

    def verify(self, output: LLMOutputV2, context: BuiltContext) -> VerificationResult:
        """Thực hiện thẩm định 2 tầng cho phản hồi LLMOutputV2 trên BuiltContext đã cấp."""
        # 1. Trường hợp từ chối do không đủ ngữ cảnh (insufficient_context)
        if output.status == "insufficient_context":
            return VerificationResult(
                passed=True,
                claim_results=[],
                citation_results=[],
                summary={
                    "status": "insufficient_context",
                    "total_claims": 0,
                    "supported_claims": 0,
                    "hallucination_detected": False,
                    "note": "Hệ thống từ chối hợp lệ khi ngữ cảnh thiếu dữ kiện."
                }
            )

        context_by_label: Dict[str, ContextChunk] = context.by_label()
        context_chunk_ids = {c.chunk_id: c for c in context.chunks}

        # ----------------------------------------------------
        # TẦNG 1: FORMAL VERIFICATION TRÊN CITATIONS
        # ----------------------------------------------------
        citation_results: List[CitationCheck] = []
        valid_citation_ids = set()
        claimed_citation_ids = set()

        for clm in output.claims:
            for cid in clm.citation_ids:
                claimed_citation_ids.add(cid)

        for cit in output.citations:
            cid = cit.get("citation_id", "")
            chunk_id = cit.get("chunk_id", "")
            article_id = cit.get("article_id", "")

            # Kiểm tra xem citation_id có tồn tại trong context không
            src_chunk = context_by_label.get(cid)
            exists_in_ctx = src_chunk is not None

            # Kiểm tra chunk_id và metadata có khớp với chunk thực tế được cấp
            chunk_id_valid = False
            metadata_valid = False
            detail_msg = []

            if exists_in_ctx and src_chunk is not None:
                chunk_id_valid = (chunk_id == src_chunk.chunk_id)
                meta = src_chunk.source_metadata()
                # Kiểm tra khớp các trường quan trọng: document_id, article_id, article
                metadata_valid = (
                    cit.get("document_id") == meta.get("document_id")
                    and cit.get("article_id") == meta.get("article_id")
                    and cit.get("article") == meta.get("article")
                )
                if not chunk_id_valid:
                    detail_msg.append(f"Lệch chunk_id (nhận: {chunk_id}, gốc: {src_chunk.chunk_id})")
                if not metadata_valid:
                    detail_msg.append(f"Lệch metadata Điều/Khoản với nguồn gốc")
            else:
                detail_msg.append(f"Mã trích dẫn '{cid}' không có trong Context được cấp")

            supports_claim = (cid in claimed_citation_ids)
            if not supports_claim:
                detail_msg.append(f"Trích dẫn '{cid}' không gắn với bất kỳ claim nào")

            is_valid = exists_in_ctx and chunk_id_valid and metadata_valid
            if is_valid:
                valid_citation_ids.add(cid)

            citation_results.append(CitationCheck(
                citation_id=cid,
                exists_in_context=exists_in_ctx,
                chunk_id_valid=chunk_id_valid,
                metadata_valid=metadata_valid,
                supports_claim=supports_claim,
                detail="; ".join(detail_msg) if detail_msg else "Hợp lệ"
            ))

        # ----------------------------------------------------
        # TẦNG 2: SEMANTIC CLAIM-CITATION VERIFICATION
        # ----------------------------------------------------
        claim_results: List[ClaimCheck] = []
        hallucination_found = False

        for clm in output.claims:
            claim_id = clm.claim_id
            claim_text = clm.text
            cids = clm.citation_ids

            # Nếu claim không gắn citation nào
            if not cids:
                hallucination_found = True
                claim_results.append(ClaimCheck(
                    claim_id=claim_id,
                    text=claim_text,
                    supported=False,
                    verdict=SemanticVerdict.UNSUPPORTED.value,
                    confidence=1.0,
                    reason="Claim không gắn trích dẫn chứng minh căn cứ pháp lý.",
                    cited_citations=[]
                ))
                continue

            # Kiểm tra xem các citation của claim có hợp lệ về nguồn không
            invalid_cids = [cid for cid in cids if cid not in valid_citation_ids]
            if invalid_cids:
                hallucination_found = True
                claim_results.append(ClaimCheck(
                    claim_id=claim_id,
                    text=claim_text,
                    supported=False,
                    verdict=SemanticVerdict.UNSUPPORTED.value,
                    confidence=1.0,
                    reason=f"Claim viện dẫn các citation không hợp lệ hoặc bịa đặt: {invalid_cids}",
                    cited_citations=cids
                ))
                continue

            # Đối chiếu ngữ nghĩa với các chunk nguồn
            best_verdict = SemanticVerdict.UNSUPPORTED
            best_score = -1.0
            reasons = []

            for cid in cids:
                src_chunk = context_by_label.get(cid)
                if src_chunk:
                    score_res = evaluate_claim_against_chunk(claim_text, src_chunk.content)
                    reasons.append(f"[{cid}]: {score_res.reason}")
                    if score_res.score > best_score:
                        best_score = score_res.score
                        best_verdict = score_res.verdict

            is_supported = (best_verdict in (SemanticVerdict.SUPPORTED, SemanticVerdict.PARTIAL))
            if not is_supported:
                hallucination_found = True

            claim_results.append(ClaimCheck(
                claim_id=claim_id,
                text=claim_text,
                supported=is_supported,
                verdict=best_verdict.value,
                confidence=0.9,
                reason=" | ".join(reasons),
                cited_citations=cids
            ))

        # ----------------------------------------------------
        # TÍNH TOÁN SUMMARY & KẾT QUẢ CUỐI CÙNG
        # ----------------------------------------------------
        total_claims = len(output.claims)
        supported_claims = sum(1 for c in claim_results if c.supported)
        total_citations = len(output.citations)
        valid_citations = len(valid_citation_ids)

        # Không gán mặc định 1.0 (100%) khi mẫu số = 0 để tránh báo cáo giả tạo.
        # Giá trị None được đưa vào summary để caller (metrics.py) ghi "chưa đo" thay vì 100%.
        correctness_rate = (valid_citations / total_citations) if total_citations > 0 else None
        coverage_rate = (supported_claims / total_claims) if total_claims > 0 else None

        # Điều kiện passed tổng:
        # 1. Không có citation bịa / sai metadata
        # 2. Không có hallucination nghiêm trọng (tất cả claim phải được supported/partial)
        all_citations_valid = all(c.exists_in_context and c.chunk_id_valid and c.metadata_valid for c in citation_results)
        passed = (not hallucination_found) and all_citations_valid

        summary = {
            "total_claims": total_claims,
            "supported_claims": supported_claims,
            "total_citations": total_citations,
            "valid_citations": valid_citations,
            # None khi mẫu số = 0 → caller ghi "chưa đo", không gán mặc định 100%
            "citation_correctness": round(correctness_rate, 4) if correctness_rate is not None else None,
            "citation_coverage": round(coverage_rate, 4) if coverage_rate is not None else None,
            "hallucination_detected": hallucination_found,
            "all_citations_valid": all_citations_valid,
        }

        return VerificationResult(
            passed=passed,
            claim_results=claim_results,
            citation_results=citation_results,
            summary=summary,
        )


def verify_response(output: LLMOutputV2, context: BuiltContext) -> VerificationResult:
    """Hàm giao diện chuẩn xác nhận theo đúng mục 4 của tasks.md:

    def verify_response(output: LLMOutputV2, context: BuiltContext) -> VerificationResult
    """
    verifier = CitationVerifier()
    return verifier.verify(output, context)
