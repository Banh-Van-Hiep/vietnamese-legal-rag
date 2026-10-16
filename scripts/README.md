# Shared Scripts

Script dùng chung của project.

| Script | Chức năng |
|---|---|
| `preprocess_legal_data.py` | Đọc `data/doanh-nghiep/registry/documents.json` và `raw/{id}/source.txt`, ghi `interim/{id}.txt`, gọi `chunk_documents.py` để ghi `processed/chunks.jsonl`. Test: `tests/test_preprocess_legal_data.py`. |
