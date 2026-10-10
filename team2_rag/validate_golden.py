import json
from pathlib import Path

CHUNKS_FILE = Path("data/doanh-nghiep/processed/chunks.jsonl")
GOLDEN_FILE = Path("team2_rag/data/golden/golden_phase1_30cai.json")


def validate_golden_dataset():
    if not CHUNKS_FILE.exists() or not GOLDEN_FILE.exists():
        print("❌ Không tìm thấy file corpus hoặc file golden!")
        return

    # 1. Load toàn bộ corpus của Team 1
    print("⏳ Đang tải cơ sở dữ liệu chunks...")
    valid_chunks = {}
    with open(CHUNKS_FILE, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                data = json.loads(line)
                if "chunk_id" in data:
                    valid_chunks[data["chunk_id"]] = data.get("content", "")

    # 2. Load file Golden Dataset của Team 2
    with open(GOLDEN_FILE, "r", encoding="utf-8") as f:
        golden_data = json.load(f)

    print(
        f"🔍 Bắt đầu kiểm tra toàn diện {len(golden_data)} mẫu golden...\n"
    )

    seen_ids = set()
    all_passed = True
    required_fields = [
        "id",
        "question",
        "expected_status",
        "ground_truth",
        "gold_chunk_ids",
        "citation",
        "category",
        "author",
    ]

    for idx, item in enumerate(golden_data, 1):
        item_id = item.get("id")
        print(f"--- Kiểm tra mẫu [{idx}] ID: {item_id} ---")
        sample_error = False

        # Kiểm tra 1: Thiếu trường bắt buộc (Missing fields)
        for field in required_fields:
            if field not in item:
                print(f"  ❌ Lỗi: Thiếu trường bắt buộc '{field}'")
                sample_error = True

        # Kiểm tra 2: Trùng lặp ID (Duplicate ID)
        if item_id in seen_ids:
            print(f"  ❌ Lỗi: Bị trùng ID '{item_id}' với mẫu trước đó!")
            sample_error = True
        else:
            seen_ids.add(item_id)

        # Kiểm tra 3: Logic trạng thái và chunk IDs
        expected_status = item.get("expected_status")
        chunk_ids = item.get("gold_chunk_ids", [])

        if expected_status == "answerable" and not chunk_ids:
            print(
                "  ❌ Lỗi: expected_status là 'answerable' nhưng mảng gold_chunk_ids lại rỗng!"
            )
            sample_error = True

        # Kiểm tra 4: Tồn tại chunk ID trong corpus
        for cid in chunk_ids:
            if cid in valid_chunks:
                print(f"  ✅ Chunk ID hợp lệ: {cid}")
            else:
                print(
                    f"  ❌ Lỗi: Chunk ID không tồn tại trong corpus của Team 1: {cid}"
                )
                sample_error = True

        if sample_error:
            all_passed = False

    print("\n" + "=" * 45)
    if all_passed:
        print(
            "🎉 TUYỆT VỜI! Tất cả các mẫu đều vượt qua kiểm tra toàn diện (Không trùng ID, đủ trường, đúng chunk ID)."
        )
    else:
        print("⚠️ PHÁT HIỆN LỖI! Vui lòng sửa lại các điểm báo lỗi ở trên.")


if __name__ == "__main__":
    validate_golden_dataset()