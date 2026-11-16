# 0001. Tám quyết định baseline v2.0

- Ngày: 2026-10-28 (baseline v2.0 được xác nhận) · Trạng thái: Accepted
- Nguồn: Google Doc "Legal RAG", mục 12.1 (DEC-01..08). Ghi lại vào repo ngày 2026-11-16.

Các quyết định này được chốt cùng lúc khi nhóm hợp nhất đặc tả v2.0, nên được giữ chung một ADR.

| Mã | Quyết định | Lý do |
| :--- | :--- | :--- |
| DEC-01 | Miền pháp luật doanh nghiệp là trung tâm; luật liên quan chỉ vào theo use case | Quyết định phạm vi mới của nhóm, thay phạm vi chỉ có luật lao động |
| DEC-02 | Làm Project 1 đầy đủ: hybrid retrieval, rerank, LLM và citation | Đề bài của giảng viên |
| DEC-03 | Java backend và Python AI service giao tiếp bằng HTTP JSON | Giữ công nghệ của Team 3, không trùng trách nhiệm |
| DEC-04 | Thư viện retrieval của Team 1 chạy chung process với AI service | Khớp thiết kế đã push, bớt một service |
| DEC-05 | Chat MVP dùng SSE `POST /api/v1/chat/stream`; chưa bắt buộc stream token từ provider | Bám skeleton GitHub; đặc tả rõ terminal, citation, error |
| DEC-06 | Public API dùng camelCase và ID số; internal JSON dùng snake_case; `clientRequestId` là UUID v4 | Java adapter giữ được RAG mock v0.1 và kiến trúc GitHub |
| DEC-07 | Hiệu lực xét theo từng đơn vị (Khoản/Điểm) và theo snapshot có review | Tránh lọc chỉ bằng `legal_status` của cả văn bản |
| DEC-08 | Mốc chất lượng: Recall@5 ≥ 85%, citation correctness ≥ 90%, answer ≥ baseline | Cụ thể hóa mốc của Project 1; đây là mục tiêu, không phải số đã đo |

## Hệ quả
- DEC-07 chưa được triển khai đầy đủ: `unit_applicability.jsonl` chưa có (xem `ARCHITECTURE.md` mục 4.3).
- Model khởi đầu (AITeamVN/Vietnamese_Embedding, BAAI/bge-reranker-v2-m3) là lựa chọn thử nghiệm; lựa chọn retrieval đã đo nằm ở ADR 0003.
