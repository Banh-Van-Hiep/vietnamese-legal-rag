# Kiểm tra cài đặt và chạy AI Service (VLRA-T2-46, VLRA-T2-48)

Ngày 25/11/2026, nhánh `feature/team2-week12-delivery` (gốc `develop` `1c6c890`). Máy: macOS (Apple Silicon), Python 3.12.15, không GPU.

## 1. Cài trong venv sạch (T2-46)

```bash
python3.12 -m venv /tmp/venv-clean
/tmp/venv-clean/bin/pip install --upgrade pip
/tmp/venv-clean/bin/pip install -r team2_rag/requirements.txt
/tmp/venv-clean/bin/pip install -e .
```

| Bước | Kết quả |
| :--- | :--- |
| Cài `team2_rag/requirements.txt` (21 gói khóa phiên bản) | Thành công |
| `pip install -e .` | Thành công (setuptools in cảnh báo về cách build editable, không ảnh hưởng) |
| `python -m team2_rag --scenario answered` (mock CLI) | Trả JSON `status=answered` kèm citation mẫu |
| `python -m pytest team2_rag/tests -q` | 368 passed |

Chưa kiểm: Linux/container (Team 3 kiểm trong VLRA-84), extras `.[dense,reranker]` (cần GPU, chưa khóa phiên bản).

## 2. Live server BM25-only (T2-48)

```bash
RAG_BM25_ONLY=true .venv/bin/python -m uvicorn team2_rag.api:create_app --factory --host 127.0.0.1 --port 8001 --workers 1
curl http://127.0.0.1:8001/internal/v1/ready
curl -H 'Content-Type: application/json' -H 'X-Request-ID: w12-smoke-2' \
  -d '{"question":"Công ty TNHH một thành viên có được phát hành cổ phần không?","history":[]}' \
  http://127.0.0.1:8001/internal/v1/query
```

| Kiểm tra | Kết quả |
| :--- | :--- |
| Khởi động tới `/internal/v1/ready` = 200 | 9 giây |
| `/internal/v1/health` | 200 |
| Câu hỏi mẫu, lần 1 | `LLM_UNAVAILABLE`: Gemini trả HTTP 503 cả 4 lần thử (2 lần model chính, 2 lần model dự phòng), 16,5 giây |
| Câu hỏi mẫu, lần 2 (sau 1 phút) | `answered`, 2 citation, 24,7 giây; 3 lần đầu vẫn 503, lần cuối thành công |

Nối dây Retrieval → Context Builder → LLM → kiểm citation hoạt động. Gemini bản miễn phí hay trả 503 khi quá tải; log `llm_http ... status=503` ghi đúng từng lần thử.

Chưa kiểm: chế độ Hybrid + Rerank (chờ index snapshot của Team 1, VLRA-82, và máy có GPU).
