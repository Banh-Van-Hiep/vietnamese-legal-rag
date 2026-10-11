"""Kiểm tra bộ Ground Truth của Team 3 theo định dạng golden của Team 2.

Chạy từ thư mục gốc repo (cần chunks.jsonl của Team 1 và, nếu có, bộ golden của Team 2):

    python -X utf8 team3_fullstack/ground_truth/validate_ground_truth.py
    python -X utf8 team3_fullstack/ground_truth/validate_ground_truth.py --chunks đường/dẫn/chunks.jsonl
    python -X utf8 team3_fullstack/ground_truth/validate_ground_truth.py --min 5 --max 10

Số mẫu: mặc định chỉ yêu cầu tối thiểu 5 mẫu và KHÔNG giới hạn tối đa, vì chỉ tiêu 5-10 câu tính theo
từng thành viên (VLRA-24) còn file này gộp nhiều người. Muốn ép giới hạn thì truyền --max.

Thoát với mã 1 nếu có lỗi, mã 0 nếu hợp lệ. Script không kiểm chứng đáp án đúng về pháp lý.
"""
import argparse
import json
import re
import sys
import unicodedata
from pathlib import Path

HERE = Path(__file__).resolve().parent
REQUIRED = ["id", "question", "expected_status", "ground_truth", "gold_chunk_ids", "citation", "category", "author"]
STATUSES = {"answered", "insufficient_context"}


def normalize(text):
    """Chuẩn hóa để bắt trùng: Unicode NFC, gộp khoảng trắng, bỏ chữ hoa/thường."""
    return re.sub(r"\s+", " ", unicodedata.normalize("NFC", str(text))).strip().lower()


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
    parser.add_argument("--min", type=int, default=5, dest="min_samples", help="số mẫu tối thiểu (mặc định 5)")
    parser.add_argument("--max", type=int, default=0, dest="max_samples", help="số mẫu tối đa; 0 = không giới hạn")
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
            other_ids.add(normalize(g.get("id", "")))
            other_questions.add(normalize(g.get("question", "")))

    if len(samples) < args.min_samples:
        errors.append(f"Cần ít nhất {args.min_samples} mẫu, hiện có {len(samples)}.")
    if args.max_samples and len(samples) > args.max_samples:
        errors.append(f"Chỉ được tối đa {args.max_samples} mẫu, hiện có {len(samples)}.")

    ids, questions = set(), set()
    for s in samples:
        sid = s.get("id", "?")
        for key in REQUIRED:
            if key not in s:
                errors.append(f"{sid}: thiếu field '{key}'.")
        nid = normalize(sid)
        if nid in ids or nid in other_ids:
            errors.append(f"{sid}: ID bị trùng.")
        ids.add(nid)
        q = normalize(s.get("question", ""))
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

    answered = sum(1 for s in samples if s.get("expected_status") == "answered")
    print(f"\nSố mẫu: {len(samples)} ({answered} answered, {len(samples) - answered} insufficient_context)")
    if errors:
        print("\nLỖI:")
        for e in errors:
            print(" -", e)
        sys.exit(1)
    print(f"Hợp lệ: {len(samples)} mẫu.")


if __name__ == "__main__":
    main()
