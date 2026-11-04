"""Rubric chấm điểm ngữ nghĩa cho trích dẫn và phát hiện Hallucination (VLRA-T2-24).

LƯU Ý VỀ PHƯƠNG PHÁP:
Đây là phương pháp thẩm định ngữ nghĩa gần đúng tầng đầu (Fast Lexical-Semantic Heuristic Filter)
kết hợp phân tích phân cực cấm đoán/quyền hạn và độ bao phủ từ vựng pháp lý. Phương pháp này có
ưu điểm tốc độ siêu nhanh (<1ms/claim), chạy inline trong request mà không tốn chi phí gọi LLM
lần 2, nhưng chưa phải Full Semantic NLI (Natural Language Inference) hay LLM-as-a-judge.

ĐỊNH NGHĨA ẢO GIÁC (HALLUCINATION):
- Claim-level Hallucination: Một nhận định pháp lý (claim) bị xếp vào UNSUPPORTED hoặc CONTRADICTED.
- Query-level Hallucination: Câu trả lời có chứa ít nhất một claim bị xếp vào UNSUPPORTED/CONTRADICTED.

Hệ thống đánh giá quan hệ Claim - Context Chunk theo chuẩn 4 mức độ:
1. SUPPORTED (Điểm 1.0):
   - Mệnh đề được chứng thực hoàn toàn từ đoạn văn bản luật được trích dẫn.
   - Các thực thể, hành vi, quyền hạn, nghĩa vụ hoặc điều kiện áp dụng đều có căn cứ trực tiếp.
2. PARTIAL (Điểm 0.5):
   - Mệnh đề phản ánh phần lớn nội dung của điều luật nhưng có thể khái quát hóa hoặc thiếu điều kiện ràng buộc.
3. UNSUPPORTED / UNGROUNDED (Điểm 0.0 - HALLUCINATION):
   - Mệnh đề đưa ra kết luận pháp lý mà đoạn trích dẫn không hề đề cập tới (suy diễn ngoài văn bản).
4. CONTRADICTED (Điểm -1.0 - CRITICAL HALLUCINATION):
   - Mệnh đề trái ngược với quy định trong đoạn luật (ví dụ: luật cấm nhưng claim khẳng định được phép).
"""
from __future__ import annotations

import enum
import re
import unicodedata
from dataclasses import dataclass
from typing import Set, Tuple


class SemanticVerdict(str, enum.Enum):
    SUPPORTED = "SUPPORTED"
    PARTIAL = "PARTIAL"
    UNSUPPORTED = "UNSUPPORTED"
    CONTRADICTED = "CONTRADICTED"


@dataclass(frozen=True)
class RubricScore:
    verdict: SemanticVerdict
    score: float
    confidence: float
    reason: str


# Các từ khóa phủ định và đối lập trong thuật ngữ pháp lý Việt Nam
_NEGATION_WORDS = {
    "không", "chưa", "chẳng", "không được", "cấm", "nghiêm cấm",
    "bãi bỏ", "hết hiệu lực", "đình chỉ", "chấm dứt", "từ chối"
}

_EXCEPTION_MARKERS = {
    "trừ trường hợp", "trừ khi", "ngoại trừ", "ngoại lệ", "trừ",
    "nếu có thỏa thuận khác", "trừ điều lệ công ty có quy định khác"
}

_LEGAL_MODALS = {
    "phải", "có nghĩa vụ", "bắt buộc", "được quyền", "có quyền", "được phép"
}


def normalize_vietnamese_text(text: str) -> str:
    """Chuẩn hóa văn bản tiếng Việt sang dạng chữ thường NFC, bỏ dấu câu thừa."""
    if not text:
        return ""
    text = unicodedata.normalize("NFC", text.lower())
    text = re.sub(r"[^\w\s\d]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def extract_content_keywords(text: str) -> Set[str]:
    """Trích xuất tập từ vựng có ý nghĩa pháp lý (bỏ các stopword quá ngắn)."""
    norm = normalize_vietnamese_text(text)
    words = norm.split()
    # Lọc bỏ các từ đệm thông thường nếu cần, giữ các từ có độ dài >= 2 ký tự
    return {w for w in words if len(w) >= 2}


def evaluate_claim_against_chunk(claim_text: str, chunk_content: str) -> RubricScore:
    """Thẩm định tính chân thực ngữ nghĩa giữa một Claim và nội dung Chunk luật tương ứng.

    Quy trình phân tích 3 bước:
    1. Kiểm tra mâu thuẫn trực tiếp (Contradiction check):
       Phát hiện sự đảo ngược về từ khóa phủ định / cấm đoán giữa claim và chunk.
    2. Kiểm tra độ bao phủ từ vựng và thực thể (Content & entity coverage):
       Tính tỷ lệ giao nhau của các từ vựng mang nghĩa pháp lý.
    3. Xác định phân loại theo Rubric:
       - Coverage >= 0.65 và không mâu thuẫn -> SUPPORTED
       - 0.40 <= Coverage < 0.65 -> PARTIAL
       - Coverage < 0.40 -> UNSUPPORTED (Hallucination)
    """
    if not claim_text.strip():
        return RubricScore(
            verdict=SemanticVerdict.UNSUPPORTED,
            score=0.0,
            confidence=1.0,
            reason="Claim rỗng, không có nội dung kiểm tra."
        )

    if not chunk_content.strip():
        return RubricScore(
            verdict=SemanticVerdict.UNSUPPORTED,
            score=0.0,
            confidence=1.0,
            reason="Nội dung chunk nguồn rỗng."
        )

    claim_norm = normalize_vietnamese_text(claim_text)
    chunk_norm = normalize_vietnamese_text(chunk_content)

    claim_words = extract_content_keywords(claim_text)
    chunk_words = extract_content_keywords(chunk_content)

    if not claim_words:
        return RubricScore(
            verdict=SemanticVerdict.UNSUPPORTED,
            score=0.0,
            confidence=1.0,
            reason="Claim không chứa từ vựng pháp lý hợp lệ."
        )

    # 1. Kiểm tra phân cực phủ định (Negation polarity)
    claim_has_negation = any(neg in claim_norm for neg in _NEGATION_WORDS)
    chunk_has_negation = any(neg in chunk_norm for neg in _NEGATION_WORDS)

    # Nếu claim phủ định mà chunk không có từ phủ định nào và ngược lại khi nói về quyền hạn
    has_polar_conflict = False
    if claim_has_negation != chunk_has_negation:
        # Kiểm tra sâu hơn nếu có từ chỉ quyền hạn / cấm đoán
        for modal in ["được quyền", "có quyền", "được thành lập", "được quản lý", "phải"]:
            if modal in claim_norm and modal in chunk_norm:
                if (claim_has_negation and not chunk_has_negation) or (not claim_has_negation and chunk_has_negation):
                    has_polar_conflict = True
                    break

    # 2. Tính tỷ lệ bao phủ từ vựng (Word overlap coverage)
    intersection = claim_words.intersection(chunk_words)
    coverage = len(intersection) / len(claim_words)

    # 3. Phân định kết quả theo Rubric
    if has_polar_conflict and coverage >= 0.4:
        return RubricScore(
            verdict=SemanticVerdict.CONTRADICTED,
            score=-1.0,
            confidence=0.9,
            reason=f"Phát hiện mâu thuẫn phân cực (phủ định/khẳng định) với điều luật. Độ trùng khớp từ vựng: {coverage:.1%}"
        )

    if coverage >= 0.60:
        return RubricScore(
            verdict=SemanticVerdict.SUPPORTED,
            score=1.0,
            confidence=min(1.0, coverage + 0.1),
            reason=f"Nội dung claim được chứng minh rõ ràng bởi chunk nguồn (Độ bao phủ: {coverage:.1%})."
        )
    elif coverage >= 0.35:
        return RubricScore(
            verdict=SemanticVerdict.PARTIAL,
            score=0.5,
            confidence=0.75,
            reason=f"Claim phản ánh một phần nội dung nhưng có thể thiếu điều kiện hoặc khái quát hóa (Độ bao phủ: {coverage:.1%})."
        )
    else:
        return RubricScore(
            verdict=SemanticVerdict.UNSUPPORTED,
            score=0.0,
            confidence=0.85,
            reason=f"Nội dung claim không tìm thấy căn cứ xác thực trong chunk được trích dẫn (Độ bao phủ chỉ đạt {coverage:.1%}). Nguy cơ Hallucination."
        )
