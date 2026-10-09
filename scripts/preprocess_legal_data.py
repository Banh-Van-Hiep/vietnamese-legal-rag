import json
import subprocess
import sys
from pathlib import Path


# Xác định thư mục gốc của project
ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data" / "doanh-nghiep"
INTERIM_DIR = DATA_DIR / "interim"
REGISTRY_FILE = DATA_DIR / "registry" / "documents.json"
CHUNK_SCRIPT = DATA_DIR / "chunk_documents.py"
OUTPUT_FILE = DATA_DIR / "processed" / "chunks.jsonl"


def validate_inputs():
    """Kiểm tra registry và dữ liệu đầu vào."""
    if not REGISTRY_FILE.is_file():
        raise FileNotFoundError(f"Không tìm thấy registry: {REGISTRY_FILE}")

    if not CHUNK_SCRIPT.is_file():
        raise FileNotFoundError(f"Không tìm thấy script chunking: {CHUNK_SCRIPT}")

    registry = json.loads(REGISTRY_FILE.read_text(encoding="utf-8"))

    if not isinstance(registry, list) or not registry:
        raise ValueError("Registry phải là danh sách tài liệu và không được rỗng.")

    seen_ids = set()

    for meta in registry:
        document_id = meta.get("document_id")

        if not document_id:
            raise ValueError("Có tài liệu thiếu document_id trong registry.")

        if document_id in seen_ids:
            raise ValueError(f"document_id bị trùng: {document_id}")
        seen_ids.add(document_id)

        input_file = INTERIM_DIR / f"{document_id}.txt"

        if not input_file.is_file():
            raise FileNotFoundError(f"Thiếu file đầu vào: {input_file}")

        if not input_file.read_text(encoding="utf-8").strip():
            raise ValueError(f"File đầu vào rỗng: {input_file.name}")

    print(f"[OK] Đã kiểm tra {len(registry)} tài liệu đầu vào.")
    return len(registry)


def run_chunking():
    """Chạy chương trình chunking hiện có."""
    print("[INFO] Bắt đầu tạo chunks...")

    subprocess.run(
        [sys.executable, str(CHUNK_SCRIPT)],
        cwd=str(ROOT),
        check=True,
    )

    if not OUTPUT_FILE.is_file():
        raise FileNotFoundError("Chunking kết thúc nhưng không tìm thấy chunks.jsonl.")

    print(f"[OK] Đã tạo file: {OUTPUT_FILE}")


def validate_output():
    """Kiểm tra định dạng và tính hợp lệ của chunks.jsonl."""
    total = 0
    seen_ids = set()
    required_fields = {
        "chunk_id",
        "document_id",
        "content",
    }

    with OUTPUT_FILE.open("r", encoding="utf-8") as file:
        for line_number, line in enumerate(file, start=1):
            if not line.strip():
                raise ValueError(f"Dòng {line_number} trong output bị rỗng.")

            try:
                chunk = json.loads(line)
            except json.JSONDecodeError as error:
                raise ValueError(
                    f"JSON không hợp lệ tại dòng {line_number}: {error}"
                ) from error

            if not isinstance(chunk, dict):
                raise ValueError(f"Dòng {line_number} không phải JSON object.")

            missing = required_fields - chunk.keys()
            if missing:
                raise ValueError(
                    f"Dòng {line_number} thiếu trường: {sorted(missing)}"
                )

            if not str(chunk["content"]).strip():
                raise ValueError(f"Chunk tại dòng {line_number} không có nội dung.")

            chunk_id = chunk["chunk_id"]
            if not chunk_id:
                raise ValueError(f"Chunk tại dòng {line_number} thiếu chunk_id.")

            if chunk_id in seen_ids:
                raise ValueError(f"chunk_id bị trùng: {chunk_id}")

            seen_ids.add(chunk_id)
            total += 1

    if total == 0:
        raise ValueError("Output không có chunk nào.")

    print(f"[OK] Đã kiểm tra {total} chunks.")
    return total


def main():
    try:
        document_count = validate_inputs()
        run_chunking()
        chunk_count = validate_output()

        print("\n=== PREPROCESSING HOÀN TẤT ===")
        print(f"Số tài liệu đầu vào: {document_count}")
        print(f"Số chunks đầu ra: {chunk_count}")
        print(f"File kết quả: {OUTPUT_FILE}")

    except (FileNotFoundError, ValueError, json.JSONDecodeError,
            subprocess.CalledProcessError) as error:
        print(f"\n[ERROR] Pipeline thất bại: {error}")
        sys.exit(1)


if __name__ == "__main__":
    main()