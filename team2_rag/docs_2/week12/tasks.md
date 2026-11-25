# Kế Hoạch Triển Khai Kỹ Thuật — Tuần 12
## Phân Hệ: RAG & LLM (Team 2)

Đối chiếu với `develop` tại `1c6c890` (25/11/2026). Tuần cuối: đóng gói AI Service để Team 3 ghép vào Docker và làm phần AI/RAG cho báo cáo cuối kỳ, slide, demo.

---

## 1. Thông Tin Chung & Mục Tiêu
- **Giai đoạn:** Tuần 12, ứng với **VLRA Sprint 9** trên Jira, từ 24/11 đến 30/11/2026.
- **Ticket Team 2:** **VLRA-83** — Đóng gói và hoàn thiện AI RAG Service, hạn 30/11/2026.
- **Ticket liên quan:** VLRA-82 (Team 1 bàn giao Data & Retrieval, index snapshot), VLRA-84 (Team 3 Docker hóa toàn hệ thống, chủ trì Final Project Report và demo).

Tiêu chí hoàn thành của VLRA-83 (Jira):
1. Module `team2_rag` cài đặt được độc lập.
2. Dependencies được cố định phiên bản.
3. API hoạt động với cấu hình hợp lệ.
4. Mock CLI và live server chạy được.
5. Có kịch bản demo và nội dung báo cáo.

### Hiện trạng trước khi làm
- `pyproject.toml` chỉ khai khoảng phiên bản (`fastapi>=0.115,<1`...), chưa có file khóa phiên bản chính xác. `requirements-week4.txt` và `team2_rag/requirements-dev.txt` đã cũ.
- Package gộp `team1_data` và `team2_rag`; `team2_rag` cần `team1_data.retrieval` khi chạy live nên "cài độc lập" nghĩa là cài từ repo mà không cần Java, Node hay Team 3.
- `team2_rag/README.md` (112 dòng) còn nội dung Tuần 4–5, chưa có bảng biến môi trường mới (`RAG_*`, `LLM_RATE_LIMIT_RPM`, `RAG_RERANK_DEVICE`, `RAG_VERIFY_CLAIMS`).
- Mock CLI có sẵn: `python -m team2_rag --scenario answered|insufficient_context`. Mock server: `team2_rag.api.mock_app:create_mock_app`. Live server: `team2_rag.api:create_app`.
- `docker-compose.yml` mới là placeholder; Dockerfile do Team 3 viết (VLRA-84) nhưng cần lệnh chạy, biến môi trường và đường dẫn index từ Team 2.
- Kết quả G5 đã có: `docs/team2_rag/g5_b0_vs_t0_report.*`, `g5_blind_evaluation_report.md`, `g5_error_analysis.md`, `g5_final_report_team2_section.md`.

---

## 2. Phân Rã Công Việc

Mã nội bộ nối tiếp Tuần 11 (kết thúc ở `VLRA-T2-44`). Tất cả thuộc **VLRA-83**.

### 2.1. Người 1 (Đạt): Đóng gói và kiểm tra chạy được

| Mã | Việc | Đạt khi |
| :--- | :--- | :--- |
| **VLRA-T2-45** | Cố định phiên bản: tạo `team2_rag/requirements.txt` (bản khóa cho AI Service: `api`, `rag`, `retrieval`) và `team2_rag/requirements-gpu.txt` (thêm `dense`, `reranker` cho T0). Xóa hoặc đánh dấu cũ các file requirements không dùng. | Mọi dòng dạng `gói==phiên_bản`. Cài trong venv mới bằng file này rồi chạy test Team 2 pass. |
| **VLRA-T2-46** | Kiểm tra cài độc lập: clone sạch, venv mới, `pip install -r team2_rag/requirements.txt && pip install -e .`, chạy mock CLI, mock server và live server BM25-only. | Có nhật ký các lệnh đã chạy và kết quả trong `docs/team2_rag/install-check.md`, ghi rõ hệ điều hành và phiên bản Python. |
| **VLRA-T2-47** | Viết lại `team2_rag/README.md`: cài đặt, cấu hình API key (chỉ trong `.env`), bảng biến môi trường, 4 chế độ chạy (mock CLI, mock server, live BM25-only, live Hybrid + Rerank), lệnh kiểm tra, lỗi thường gặp (429/503, thiếu index, rerank trên CPU). | Bảng biến môi trường khớp `configs/team2-api.env.example` và code; người ngoài nhóm làm theo chạy được. |
| **VLRA-T2-48** | Kiểm tra nối dây Retrieval → Reranker → Context Builder → LLM: một lệnh kiểm tra nhanh (`/internal/v1/ready` + một câu hỏi mẫu) cho cả BM25-only và Hybrid + Rerank. Bàn giao Team 3 cho VLRA-84: lệnh khởi động, biến môi trường, đường dẫn index, healthcheck. | Team 3 chạy được AI Service trong container theo bàn giao. Ghi lại kết quả câu hỏi mẫu (status, số citation, thời gian). |

### 2.2. Người 2 (Hiệp): Báo cáo, slide và demo

| Mã | Việc | Đạt khi |
| :--- | :--- | :--- |
| **VLRA-T2-49** | Viết phần AI & RAG cho Final Project Report: kiến trúc pipeline, prompt và citation, verification, kết quả G5 (định lượng + chấm mù + phân tích lỗi), NFR-07/08/09, giới hạn. Dựa trên các báo cáo đã có, không đo lại. | Mọi con số trích từ file trong `docs/team2_rag/`, có đường dẫn nguồn. Gửi Team 3 ghép vào báo cáo chung (VLRA-84). |
| **VLRA-T2-50** | Làm slide phần AI & RAG (5–7 slide). | Slide dùng đúng số liệu của T2-49. |
| **VLRA-T2-51** | Kịch bản demo có và không có Reranker: chọn 3–4 câu từ Test Set có kết quả B0/T0 khác nhau (ví dụ T0 tốt hơn: `test_062`, `test_020`, `test_049`; T0 kém hơn: `test_052`), lấy câu trả lời đã lưu trong `docs/team2_rag/runs/g5/`. | Kịch bản ghi rõ câu hỏi, câu trả lời mỗi bên, lý do khác nhau (theo `g5_error_analysis.md`), và cách chạy lại nếu có GPU. |

### 2.3. Chung
- **VLRA-T2-52:** Phối hợp demo end-to-end với Team 3 (VLRA-84): chạy thử trên máy sạch trước buổi demo, chốt chế độ demo (BM25-only trên CPU hay Hybrid + Rerank trên GPU).

### 2.4. Thứ tự phụ thuộc
1. T2-45 → T2-46 → T2-48 (bàn giao Team 3 càng sớm càng tốt vì VLRA-84 cần để viết Dockerfile).
2. T2-47 làm song song, chốt sau T2-46.
3. T2-49 → T2-50. T2-51 độc lập, dùng kết quả đã lưu.

---

## 3. Đặc Tả

### 3.1. Chế độ chạy AI Service

| Chế độ | Lệnh | Cần |
| :--- | :--- | :--- |
| Mock CLI | `python -m team2_rag --scenario answered` | Không cần key, không cần index |
| Mock server | `RAG_MOCK_SCENARIO=answered_markdown python -m uvicorn team2_rag.api.mock_app:create_mock_app --factory --port 8001` | Không cần key |
| Live BM25-only | `RAG_BM25_ONLY=true python -m uvicorn team2_rag.api:create_app --factory --host 127.0.0.1 --port 8001` | `GEMINI_API_KEY`, `LLM_PROVIDER`, `LLM_MODEL`, file chunks |
| Live Hybrid + Rerank | như trên, bỏ `RAG_BM25_ONLY`, thêm `RAG_BM25_INDEX`, `RAG_DENSE_INDEX`, `RAG_QDRANT_PATH`, `RAG_RERANK=true`, `RAG_RERANK_DEVICE` | Index Dense/BM25 của Team 1 (VLRA-82), khoảng 2 GB RAM cho BGE, nên có GPU |

### 3.2. Quy tắc giữ nguyên khi đóng gói
- Không đổi contract (`contracts/v0.1/`), mã lỗi, chuỗi timeout 45 < 50 < 60 giây, hàng đợi 1 lượt chạy + 4 lượt chờ.
- Secret chỉ ở `.env` hoặc biến môi trường của container, không commit, không in ra log.
- Mọi thay đổi vào `develop` qua PR có review, chạy `scripts/harness_verify.py` trước khi mở PR.

---

## 4. Rủi Ro & Việc Cần Chốt

| # | Vấn đề | Ảnh hưởng | Hướng xử lý |
| :--- | :--- | :--- | :--- |
| 1 | Demo Hybrid + Rerank cần GPU và index Dense | Máy demo có thể không chạy được T0 live | Mặc định demo BM25-only live; phần có/không Reranker dùng kết quả đã lưu (T2-51) |
| 2 | Gemini bản miễn phí giới hạn 15 request/phút, hay báo 503 | Demo bị lỗi giữa chừng | Giữ `LLM_RATE_LIMIT_RPM=12`; chuẩn bị mock server làm phương án dự phòng |
| 3 | `torch` CPU/GPU khác nhau theo máy | File khóa GPU không cài được trên máy không có CUDA | Tách `requirements.txt` (không torch) và `requirements-gpu.txt` |
| 4 | ADR 0004 (hàng đợi) vẫn ghi Proposed | Tài liệu lệch với code | Nhóm chốt và đổi sang Accepted trong tuần |
| 5 | Index snapshot của Team 1 (VLRA-82) chưa bàn giao | T2-48 chế độ Hybrid chưa kiểm được | Kiểm BM25-only trước; Hybrid kiểm khi VLRA-82 xong |

---

## 5. Lệnh Kiểm Chứng

```bash
.venv/bin/python scripts/harness_verify.py
.venv/bin/python -m pytest team2_rag/tests -q
.venv/bin/python -m team2_rag --scenario answered
```

---

## 6. Trạng Thái Thực Thi (cập nhật ngày 25/11/2026)

| Mã | Jira | Người phụ trách | Trạng thái | Ghi chú |
| :--- | :--- | :--- | :---: | :--- |
| `VLRA-T2-45` | VLRA-83 | Người 1 | TODO | |
| `VLRA-T2-46` | VLRA-83 | Người 1 | TODO | Cần T2-45. |
| `VLRA-T2-47` | VLRA-83 | Người 1 | TODO | |
| `VLRA-T2-48` | VLRA-83 | Người 1 | TODO | Hybrid cần index của VLRA-82. |
| `VLRA-T2-49` | VLRA-83 | Người 2 | TODO | |
| `VLRA-T2-50` | VLRA-83 | Người 2 | TODO | Cần T2-49. |
| `VLRA-T2-51` | VLRA-83 | Người 2 | TODO | |
| `VLRA-T2-52` | VLRA-83, VLRA-84 | Chung | TODO | Cần T2-48. |
