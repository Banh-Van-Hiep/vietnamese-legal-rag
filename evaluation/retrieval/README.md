# Đánh giá Retrieval (Team 1, VLRA-48)

Pipeline tái lập được: nhiều cấu hình BM25 / Dense / Hybrid RRF chạy trên **cùng một Dev Set cố định**,
mỗi cấu hình lưu riêng cấu hình + chỉ số + kết quả từng câu; cả lần chạy có nhật ký và thông tin môi trường.

## 1. Kiểm tra dữ liệu đầu vào (chạy trước mỗi lần đánh giá)
```bash
python -m team1_data.evaluation check            # mặc định: team1_data/golden/golden_phase1.json + chunks.jsonl
```
In ra sha256 của Dev Set và corpus, số câu/gold, số Khoản trùng nguyên văn được gộp, phân bố gold theo văn bản.
Báo lỗi (exit ≠ 0) khi: golden sai schema (`id`/`question` trùng, `expected_status` lệch `gold_chunk_ids`),
gold_chunk_id không có trong corpus, gold bị loại bởi bộ lọc `legal_status`, corpus trùng `chunk_id`.
Hai lần so sánh chỉ hợp lệ khi `dev_set.sha256` và `corpus.sha256` trong `run.json` giống nhau.

## 2. Chạy đánh giá
```bash
python -m team1_data.evaluation run --config evaluation/retrieval/configs/vlra49_methods.json --run-id vlra49
```
Kết quả: `evaluation/retrieval/runs/<run-id>/`
- `<tên cấu hình>.json` — cấu hình, `metrics`, `metrics_strict_chunk_id`, latency p50/p95, thời gian build, từng câu (top-5, gold).
- `run.json` — commit, sha256 Dev Set/corpus, phiên bản thư viện, tóm tắt mọi cấu hình.
- `run.log` — nhật ký từng bước. `summary.md` — bảng so sánh.

## 3. Cấu hình (`configs/*.json`, danh sách object)
| Khóa | Ý nghĩa | Mặc định |
|---|---|---|
| `name` | tên file kết quả, duy nhất | bắt buộc |
| `method` | `bm25` / `dense` / `hybrid_rrf` | bắt buộc |
| `bm25` | `{"k1", "b"}` | 1.2 / 0.75 |
| `embedder` | `{"type": "lsa", "dim"}` · `{"type": "hash", "dim"}` · `{"type": "sentence_transformers", "name", "revision", "query_prefix", "passage_prefix"}` | lsa 256 |
| `rrf_k`, `weights` | tham số Hybrid RRF | 60, [1, 1] |
| `chunking` | `{"size": số token, "overlap": số token}`; `size` null = giữ chunk gốc theo Khoản | null |

## 4. Chỉ số
Recall@5/10/20, MRR@20 trên top-20, tính theo **Khoản** (chunk_id bỏ `__<chunk_index>`), các Khoản nội dung
nguyên văn giống nhau cùng Điều/Khoản (vd Luật 59/2020 ↔ VBHN 67) coi là một — để so được các cách chunk
khác nhau và không phạt khi trả bản hợp nhất thay bản gốc. `metrics_strict_chunk_id` = so khớp chunk_id gốc.
Mỗi đầu ra đều được kiểm tra theo `contracts/v0.1/retrieval_output.schema.json` (`scripts/eval_retrieval.py::validate_output`).

Phụ thuộc thêm: `pip install scikit-learn` (embedder `lsa`). Embedder `lsa`/`hash` chạy offline (không tải model); model thật dùng `sentence_transformers` khi có mạng tới HuggingFace.
