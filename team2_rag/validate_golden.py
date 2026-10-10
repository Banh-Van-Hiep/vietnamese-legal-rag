import json
from pathlib import Path

chunks_file = Path("data/doanh-nghiep/processed/chunks.jsonl")
golden_file = Path("team2_rag/data/golden/golden_phase1_30cai.json")

# Load toàn bộ chunk_id hợp lệ từ dữ liệu của Team 1
valid_chunks = set()
with open(chunks_file, "r", encoding="utf-8") as f:
    for line in f:
        if line.strip():
            data = json.loads(line)
            if "chunk_id" in data:
                valid_chunks.add(data["chunk_id"])

# Load file Golden Dataset của bạn
with open(golden_file, "r", encoding="utf-8") as f:
    golden_data = json.load(f)

print(f"Đang kiểm tra {len(golden_data)} mẫu golden so với {len(valid_chunks)} chunks...")

# Tiến hành kiểm tra đối chiếu
for item in golden_data:
    item_id = item.get("id")
    chunk_ids = item.get("gold_chunk_ids", [])
    for cid in chunk_ids:
        if cid in valid_chunks:
            print(f"Sample {item_id}: ✅ Hợp lệ ({cid})")
        else:
            print(f"Sample {item_id}: ❌ Sai Chunk ID ({cid})")