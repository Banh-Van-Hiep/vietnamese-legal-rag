"""Kiểm tra tính nhất quán của data/doanh-nghiep/processed/chunks.jsonl.

Đọc processed/chunks.jsonl và registry/documents.json, không ghi gì.
Kiểm tra:
  1. mọi document_id của chunk đều có bản ghi trong registry;
  2. chunk_id không trùng và đúng mẫu metadata-specification.md mục 4.4;
  3. context_header khớp công thức chunk-format-spec.md mục 4 với các
     trường cấu trúc của chính chunk đó;
  4. token_count khớp với context_header + "\\n" + content;
  5. không còn marker chú thích hợp nhất `[n]` trong content, article_title
     hay context_header (Data Processing Flow, C8);
  6. không còn từ bị chèn dấu cách giữa từ ("ngườ i" thay vì "người").
Sau đó in bảng thống kê chapter/section/amendment_notes theo từng document_id.

Chạy: python scripts/validate_chunks.py
Thoát 0 nếu pass, 1 nếu có lỗi.
"""

from __future__ import annotations

import json
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CHUNKS = ROOT / "data" / "doanh-nghiep" / "processed" / "chunks.jsonl"
REGISTRY = ROOT / "data" / "doanh-nghiep" / "registry" / "documents.json"

RE_CHUNK_ID = re.compile(r"^[a-z0-9-]+__dieu-[0-9a-z]+__k[0-9a-z]+__\d+$")
MAX_REPORT = 5

# C8: marker chú thích hợp nhất phải nằm ở amendment_notes, không ở text tìm kiếm.
RE_FOOTNOTE_MARK = re.compile(r"\[\d{1,2}\]")
# Bốn từ bị bản HTML của VBHN 67 chèn dấu cách; chunk_documents.py nối lại.
SPLIT_WORDS = ("ngườ i", "Ngườ i", "dướ i", "T rong")
RE_SPLIT_WORDS = tuple(
    re.compile(r"\b" + re.escape(bad) + r"\b") for bad in SPLIT_WORDS
)


def token_count(text: str) -> int:
    return max(1, len(re.findall(r"\S+", text)))


def build_context_header(chunk: dict) -> str:
    parts = [f"{chunk['document_title']} {chunk['document_number']}"]
    for level, title in (("chapter", "chapter_title"), ("section", "section_title")):
        if chunk[level]:
            bit = chunk[level]
            if chunk[title]:
                bit += f". {chunk[title]}"
            parts.append(bit)
    dieu = chunk["article"]
    if chunk["article_title"]:
        dieu += f". {chunk['article_title']}"
    parts.append(dieu)
    return " > ".join(parts)


def main() -> int:
    # Thông báo lỗi có tiếng Việt, console Windows mặc định cp1252 sẽ chết.
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    chunks = [json.loads(line) for line in CHUNKS.read_text(encoding="utf-8").splitlines() if line]
    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    known = {meta["document_id"] for meta in registry}

    errors: list[str] = []

    orphans = sorted({c["document_id"] for c in chunks} - known)
    if orphans:
        errors.append(f"document_id không có trong registry: {orphans}")

    ids = [c["chunk_id"] for c in chunks]
    dups = sorted({i for i, n in Counter(ids).items() if n > 1})
    if dups:
        errors.append(f"chunk_id trùng ({len(dups)}): {dups[:MAX_REPORT]}")
    malformed = [i for i in ids if not RE_CHUNK_ID.match(i)]
    if malformed:
        errors.append(f"chunk_id sai mẫu ({len(malformed)}): {malformed[:MAX_REPORT]}")

    bad_header = []
    bad_tokens = []
    for chunk in chunks:
        expected = build_context_header(chunk)
        if chunk["context_header"] != expected:
            bad_header.append(chunk["chunk_id"])
        elif chunk["token_count"] != token_count(expected + "\n" + chunk["content"]):
            bad_tokens.append(chunk["chunk_id"])
    if bad_header:
        errors.append(f"context_header lệch ({len(bad_header)}): {bad_header[:MAX_REPORT]}")
    if bad_tokens:
        errors.append(f"token_count lệch ({len(bad_tokens)}): {bad_tokens[:MAX_REPORT]}")

    leftover_mark = []
    leftover_split = []
    for chunk in chunks:
        searchable = f"{chunk['content']} {chunk['article_title'] or ''} {chunk['context_header']}"
        if RE_FOOTNOTE_MARK.search(searchable):
            leftover_mark.append(chunk["chunk_id"])
        if any(pattern.search(searchable) for pattern in RE_SPLIT_WORDS):
            leftover_split.append(chunk["chunk_id"])
    if leftover_mark:
        errors.append(
            f"còn marker chú thích [n] trong text tìm kiếm ({len(leftover_mark)}): "
            f"{leftover_mark[:MAX_REPORT]}"
        )
    if leftover_split:
        errors.append(
            f"còn từ bị chèn dấu cách ({len(leftover_split)}): {leftover_split[:MAX_REPORT]}"
        )

    order = [meta["document_id"] for meta in registry]
    stats = {doc: [0, 0, 0, 0] for doc in order}
    for chunk in chunks:
        row = stats.setdefault(chunk["document_id"], [0, 0, 0, 0])
        row[0] += 1
        if chunk["chapter"]:
            row[1] += 1
        if chunk["section"]:
            row[2] += 1
        if chunk["amendment_notes"]:
            row[3] += 1

    width = max(len(doc) for doc in stats)
    print(f"{'document_id'.ljust(width)}  {'chunks':>7}  {'chapter':>7}  "
          f"{'section':>7}  {'notes':>7}")
    for doc, (total, chapter, section, notes) in stats.items():
        print(f"{doc.ljust(width)}  {total:>7}  {chapter:>7}  {section:>7}  {notes:>7}")
    total = sum(row[0] for row in stats.values())
    print(f"{'TOTAL'.ljust(width)}  {total:>7}  "
          f"{sum(r[1] for r in stats.values()):>7}  "
          f"{sum(r[2] for r in stats.values()):>7}  "
          f"{sum(r[3] for r in stats.values()):>7}")

    if errors:
        print("\nFAIL")
        for err in errors:
            print(f"  - {err}")
        return 1
    print(f"\nPASS: {total} chunks, {len(known)} documents")
    return 0


if __name__ == "__main__":
    sys.exit(main())
