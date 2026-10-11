"""Kiểm tra bộ Ground Truth của Team 3 theo định dạng golden của Team 2.

Chạy từ thư mục gốc repo (cần chunks.jsonl của Team 1 và, nếu có, bộ golden của Team 2):

    python team3_fullstack/ground_truth/validate_ground_truth.py
    python team3_fullstack/ground_truth/validate_ground_truth.py --chunks đường/dẫn/chunks.jsonl

Thoát với mã 1 nếu có lỗi.
"""
import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REQUIRED = ["id", "question", "expected_status", "ground_truth", "gold_chunk_ids", "citation", "category", "author"]
STATUSES = {"answered", "insufficient_context"}


def load_chunks(path):
    chunks = {}
    with open(path, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                row = json.loads(line)
                chunks[row["chunk_id"]] = row
    return chunks


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--gt", default=str(HERE / "team3_ground_truth.json"))
    parser.add_argument("--chunks", default="data/doanh-nghiep/processed/chunks.jsonl")
    parser.add_argument("--team2", default="team2_rag/data/golden/golden_phase1_30cai.json")
    args = parser.parse_args()

    samples = json.loads(Path(args.gt).read_text(encoding="utf-8"))
    errors = []

    chunks = {}
    if Path(args.chunks).exists():
        chunks = load_chunks(args.chunks)
        print(f"Đã nạp {len(chunks)} chunk từ {args.chunks}")
    else:
        errors.append(f"Không thấy {args.chunks}: không đối chiếu được gold_chunk_ids (dùng --chunks).")

    other_ids, other_questions = set(), set()
    if Path(args.team2).exists():
        for g in json.loads(Path(args.team2).read_text(encoding="utf-8")):
            other_ids.add(g.get("id"))
            other_questions.add(g.get("question", "").strip().lower())

    if not 5 <= len(samples) <= 10:
        errors.append(f"Cần 5-10 mẫu, hiện có {len(samples)}.")

    ids, questions = set(), set()
    for s in samples:
        sid = s.get("id", "?")
        for key in REQUIRED:
            if key not in s:
                errors.append(f"{sid}: thiếu field '{key}'.")
        if sid in ids or sid in other_ids:
            errors.append(f"{sid}: ID bị trùng.")
        ids.add(sid)
        q = s.get("question", "").strip().lower()
        if q in questions or q in other_questions:
            errors.append(f"{sid}: câu hỏi trùng với mẫu khác.")
        questions.add(q)
        if s.get("expected_status") not in STATUSES:
            errors.append(f"{sid}: expected_status phải là {sorted(STATUSES)}.")
        gold = s.get("gold_chunk_ids", [])
        if s.get("expected_status") == "answered" and not gold:
            errors.append(f"{sid}: mẫu answered phải có gold_chunk_ids.")
        if s.get("expected_status") == "insufficient_context" and gold:
            errors.append(f"{sid}: mẫu insufficient_context phải có gold_chunk_ids rỗng.")
        for cid in gold:
            if chunks and cid not in chunks:
                errors.append(f"{sid}: chunk_id không có trong corpus: {cid}")
            else:
                print(f"{sid}: OK {cid}" if chunks else f"{sid}: (chưa đối chiếu) {cid}")
        if not gold:
            print(f"{sid}: OK (không cần chunk)")

    if errors:
        print("\nLỖI:")
        for e in errors:
            print(" -", e)
        sys.exit(1)
    print(f"\nHợp lệ: {len(samples)} mẫu.")


if __name__ == "__main__":
    main()
