# Kiểm chứng VLRA-44 — E2E giao diện MVP

**Ngày chạy:** 25/10/2026 20:00 (Asia/Saigon), commit `f790276`.
**Kết luận:** mức **G2 (mock integration) đạt 10/10**. Mức **G4 (live RAG) chưa chạy**, chưa nghiệm thu toàn bộ VLRA-44.

## 1. Môi trường

Windows, JDK 25.0.4.1, Node 22.19.0, Python 3.14 (`pip install -e ".[api,test]"`), Edge headless (profile riêng),
PostgreSQL 16 trong Docker (container tạm `vlra44-pg`, database `legal_rag_e2e`, xóa sau khi chạy).
Cổng: Frontend 15173, Java 18043, FastAPI mock 18044, DevTools 19242. `VITE_MOCK_MODE=true`.

```powershell
powershell -ExecutionPolicy Bypass -File team3_fullstack\run-vlra44-e2e.ps1 -UseDocker
```

Với PostgreSQL cài sẵn: `-DbUser postgres -DbPassword "<mật khẩu>" -CreateDb`. Thêm `-JavaHome` nếu JDK 25 không ở PATH.

## 2. Kết quả

| Ca | Nội dung | Kết quả |
| --- | --- | --- |
| E01 | Java `/api/v1/health` 200; FastAPI mock `/internal/v1/ready` 200, `X-RAG-Mode: mock` | PASS |
| E02 | Hỏi lượt đầu: câu trả lời và 1 trích dẫn từ Python, URL `/c/1`, sidebar có tiêu đề, nhãn dữ liệu thử nghiệm | PASS |
| E03 | Bấm `[C1]`: Viewer hiện nguyên văn giả lập từ Python, nguồn `https://example.com/mock-law`; public article đủ 6 trường camelCase | PASS |
| E04 | Hỏi tiếp: giữ `conversationId`, PostgreSQL có 4 tin nhắn completed theo thứ tự | PASS |
| E05 | Tải lại hội thoại: 2 câu trả lời, 2 thẻ trích dẫn, không gửi thêm request | PASS |
| E06 | `art2` → 404 `ARTICLE_NOT_FOUND`, `other_v1` → 404 `DOCUMENT_NOT_FOUND`; UI báo "Không mở được nguyên văn" | PASS |
| E07 | Python chạy kịch bản `insufficient_context`: thông báo "Chưa đủ căn cứ", 0 trích dẫn, lưu `answerStatus` đúng | PASS |
| E08 | Dừng Python: UI báo `SERVICE_UNAVAILABLE`, lượt `failed` được lưu, Viewer trả 503 | PASS |
| E09 | Bật lại Python, bấm Thử lại: lượt mới với UUID mới, lịch sử `failed` rồi `completed` | PASS |
| E10 | 5 request public đều camelCase, UUID v4, không `history`/`scenario`; 0 lỗi JavaScript | PASS |

Log của FastAPI mock xác nhận request thật đi qua ba tầng: 4 lần `POST /internal/v1/query` 200 (E02, E04, E07, E09),
3 lần article 200, 3 lần `art2` 404, 1 lần `other_v1` 404, không có query nào trong lúc service dừng (E08).

Evidence (không commit): `team3_fullstack/backend/target/vlra44-e2e/` gồm `results.json`, `rag-mock.log`,
`backend.log`, `vite.log`, `browser.png`.

## 3. Vấn đề phát hiện và đã xử lý

- **Múi giờ:** Windows ở Việt Nam báo `Asia/Saigon`; PostgreSQL 16 từ chối khi Java kết nối
  (`FATAL: invalid value for parameter "TimeZone"`). Runner chạy Java với `-Duser.timezone=UTC`. Ai chạy profile `rag`
  bằng tay trên Windows cũng cần thêm tham số này (hoặc đặt `TZ`/`JAVA_TOOL_OPTIONS`).
- Không phát hiện lệch contract Java ↔ Python: route, field, mã lỗi khớp sau PR #35 của Team 2.

## 4. Chưa đạt / còn chờ (G4 live)

| Điều kiện | Chủ trì | Hiện trạng 25/10 |
| --- | --- | --- |
| Index BM25 và Dense (Qdrant) cùng phiên bản chunk | Team 1 | Chưa build; lệnh có trong `week4-integration.md` |
| `data/doanh-nghiep/processed/articles.jsonl` cho Viewer | Team 1 | Chưa có trên `develop`; thiếu thì Viewer live trả 503 |
| Cấu hình LLM/provider và API key | Team 2 | Chưa có lần chạy live được ghi nhận |
| Chạy lại 10 ca với `create_app` + kiểm tra trích dẫn khớp nguyên văn | Team 3 | Chờ ba mục trên |

Không dùng kết quả mock để kết luận chất lượng câu trả lời hay độ đúng pháp lý.
