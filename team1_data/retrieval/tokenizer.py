"""Vietnamese tokenizer for BM25, theo docs/team1_data/bm25-proposal.md mục 3.

Các bước: T1 NFC, T2 chữ thường, T3 quy kiểu đặt dấu oa/oe/uy,
T4 giữ cụm pháp lý thành một token, T5 tách từ bằng underthesea.
"""

from __future__ import annotations

import re
import unicodedata

from underthesea import word_tokenize

TONE_MAP = {
    "oà": "òa", "oá": "óa", "oả": "ỏa", "oã": "õa", "oạ": "ọa",
    "oè": "òe", "oé": "óe", "oẻ": "ỏe", "oẽ": "õe", "oẹ": "ọe",
    "uỳ": "ùy", "uý": "úy", "uỷ": "ủy", "uỹ": "ũy", "uỵ": "ụy",
}
# Chỉ đổi khi vần đứng cuối âm tiết và không đi sau "q": "hoàng", "quỷ" giữ nguyên.
TONE_RE = re.compile(r"(?<!q)(?:" + "|".join(TONE_MAP) + r")(?!\w)")

# Số hiệu giữ nguyên dạng "59/2020/qh14"; Điều/Khoản/Điểm/Chương nối bằng "_".
LEGAL_PATTERNS = [
    (re.compile(r"\d+/\d{4}/[a-zđ0-9-]+"), lambda m: m.group(0)),
    (re.compile(r"\b(điều|khoản|điểm|chương)\s+(\d+[a-z]?|[a-zđ]|[ivxlc]+)\b"),
     lambda m: f"{m.group(1)}_{m.group(2)}"),
]


def _segment(text: str) -> list[str]:
    return word_tokenize(text, format="text").split() if text.strip() else []


def tokenize_vi(text: str) -> list[str]:
    """Trả danh sách token đã chuẩn hóa; bỏ token chỉ gồm dấu câu.

    Cụm pháp lý được cắt ra trước, phần chữ còn lại mới đưa vào underthesea,
    để underthesea không ghép hay tách các cụm này.
    """
    text = unicodedata.normalize("NFC", text).lower()
    text = TONE_RE.sub(lambda m: TONE_MAP[m.group(0)], text)

    spans: list[tuple[int, int, str]] = []
    for pattern, render in LEGAL_PATTERNS:
        for m in pattern.finditer(text):
            if all(m.end() <= s or m.start() >= e for s, e, _ in spans):
                spans.append((m.start(), m.end(), render(m)))
    spans.sort()

    tokens: list[str] = []
    pos = 0
    for start, end, legal in spans:
        tokens += _segment(text[pos:start])
        tokens.append(legal)
        pos = end
    tokens += _segment(text[pos:])
    return [t for t in tokens if any(c.isalnum() for c in t)]
