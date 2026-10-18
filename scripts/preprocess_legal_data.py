"""Chạy lại corpus doanh nghiệp: làm sạch raw, tách chunk, ghi báo cáo.

Đọc data/doanh-nghiep/registry/documents.json để biết danh sách văn bản.
Với mỗi document_id, đọc raw/{id}/source.txt, ghi interim/{id}.txt,
rồi gọi chunk_document() để ghi processed/chunks.jsonl.
"""

from __future__ import annotations

import importlib.util
import json
import re
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data" / "doanh-nghiep"
CHUNKER_FILE = DATA_DIR / "chunk_documents.py"


def load_chunker():
    """Nạp chunk_documents.py. Thư mục doanh-nghiep có gạch ngang nên không import bằng tên gói."""
    spec = importlib.util.spec_from_file_location("enterprise_chunk_documents", CHUNKER_FILE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


chunk_documents = load_chunker()
SCHEMA_FILE = (
    ROOT / "docs" / "team1_data" / "schemas" / "chunk_metadata.schema.json"
)
INVISIBLE = {"\u200b", "\ufeff", "\u00ad"}


def clean_text(text: str) -> str:
    """Chuẩn hóa Unicode và xóa ký tự rác. Không sửa câu chữ luật."""
    text = unicodedata.normalize("NFC", text)
    text = text.replace("\u00a0", " ").replace("\t", " ")
    kept = []
    for char in text:
        if char in INVISIBLE:
            continue
        if char != "\n" and unicodedata.category(char) == "Cc":
            continue
        kept.append(char)
    lines = []
    blank = 0
    for line in "".join(kept).splitlines():
        line = re.sub(r" {2,}", " ", line).strip()
        if not line:
            blank += 1
            if blank <= 1:
                lines.append("")
            continue
        blank = 0
        lines.append(line)
    cleaned = "\n".join(lines).strip()
    return cleaned + "\n" if cleaned else ""


def load_registry(data_dir: Path) -> list[dict]:
    path = data_dir / "registry" / "documents.json"
    registry = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(registry, list) or not registry:
        raise ValueError(f"Registry rỗng hoặc sai kiểu: {path}")
    seen = set()
    for meta in registry:
        document_id = meta.get("document_id")
        if not document_id:
            raise ValueError("Có mục registry thiếu document_id")
        if document_id in seen:
            raise ValueError(f"document_id bị trùng: {document_id}")
        seen.add(document_id)
    return registry


def required_fields() -> set[str]:
    if not SCHEMA_FILE.is_file():
        return {"chunk_id", "document_id", "content"}
    schema = json.loads(SCHEMA_FILE.read_text(encoding="utf-8"))
    return set(schema.get("required", []))


def validate_chunks(chunks: list[dict], fields: set[str]) -> list[str]:
    errors = []
    seen = set()
    for index, chunk in enumerate(chunks, start=1):
        missing = fields - chunk.keys()
        if missing:
            errors.append(f"chunk {index} thiếu {sorted(missing)}")
        content = str(chunk.get("content", "")).strip()
        if not content:
            errors.append(f"chunk {index} không có nội dung")
        chunk_id = chunk.get("chunk_id")
        if not chunk_id:
            errors.append(f"chunk {index} thiếu chunk_id")
        elif chunk_id in seen:
            errors.append(f"chunk_id trùng: {chunk_id}")
        else:
            seen.add(chunk_id)
    return errors


def run(data_dir: Path = DATA_DIR) -> dict:
    registry = load_registry(data_dir)
    fields = required_fields()
    all_chunks = []
    documents = []
    errors = []

    for meta in registry:
        document_id = meta["document_id"]
        raw_path = data_dir / "raw" / document_id / "source.txt"
        interim_path = data_dir / "interim" / f"{document_id}.txt"
        if raw_path.is_file():
            cleaned = clean_text(raw_path.read_text(encoding="utf-8"))
        elif interim_path.is_file():
            cleaned = clean_text(interim_path.read_text(encoding="utf-8"))
        else:
            errors.append(f"Thiếu raw và interim: {document_id}")
            documents.append(
                {
                    "document_id": document_id,
                    "chunk_count": 0,
                    "errors": [f"Thiếu file nguồn: {document_id}"],
                }
            )
            continue
        if not cleaned.strip():
            errors.append(f"Văn bản rỗng sau khi làm sạch: {document_id}")
            documents.append(
                {
                    "document_id": document_id,
                    "chunk_count": 0,
                    "errors": ["Văn bản rỗng"],
                }
            )
            continue
        interim_path.parent.mkdir(parents=True, exist_ok=True)
        interim_path.write_text(cleaned, encoding="utf-8", newline="\n")
        chunks = chunk_documents.chunk_document(meta, cleaned)
        doc_errors = validate_chunks(chunks, fields)
        documents.append(
            {
                "document_id": document_id,
                "chunk_count": len(chunks),
                "errors": doc_errors,
            }
        )
        if doc_errors:
            errors.extend(f"{document_id}: {item}" for item in doc_errors)
            continue
        all_chunks.extend(chunks)

    id_errors = validate_chunks(all_chunks, fields)
    errors.extend(id_errors)
    out_path = data_dir / "processed" / "chunks.jsonl"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8", newline="\n") as handle:
        for chunk in all_chunks:
            handle.write(json.dumps(chunk, ensure_ascii=False) + "\n")

    report = {
        "pipeline_version": "1.0.0",
        "document_count": len(registry),
        "chunk_count": len(all_chunks),
        "documents": documents,
        "errors": errors,
    }
    report_path = data_dir / "processed" / "processing_report.json"
    report_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return report


def main() -> None:
    # Console Windows mặc định cp1252 sẽ lỗi khi in tiếng Việt sau khi đã ghi xong file.
    sys.stdout.reconfigure(encoding="utf-8")
    try:
        report = run()
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(f"[ERROR] {error}")
        sys.exit(1)
    print(
        f"[OK] {report['document_count']} văn bản, {report['chunk_count']} chunks"
    )
    if report["errors"]:
        print(f"[ERROR] {len(report['errors'])} lỗi")
        sys.exit(1)


if __name__ == "__main__":
    main()
