# Kiểm chứng VLRA-43 — UI câu trả lời, căn cứ và Viewer

**Ngày:** 24/10/2026. **Kết luận:** giao diện đáp ứng FR-01…FR-11 khi kiểm bằng API public giả lập đúng shape Docs v2.0.
**Chưa nghiệm thu với RAG thật** (chờ Team 2, VLRA-44). `npm test` và `npm run build` đã PASS trên Windows (mục 3);
còn smoke VLRA-42 với Java profile `rag`.

## 1. Môi trường

Môi trường kiểm tra không tải được gói npm (registry bị chặn), nên dùng `node_modules` hiện có của dự án
(cài trên Windows) cho phần JavaScript thuần, và công cụ có sẵn thay cho các binary native của Vite/Tailwind:

| Kiểm tra | Cách chạy | Kết quả |
| --- | --- | --- |
| TypeScript | `node node_modules/typescript/bin/tsc -b` (tsconfig dự án, strict) | PASS, 0 lỗi |
| Unit test mới | `answerFormat.test.ts` + `legalCitation.test.ts`, bundle bằng esbuild và chạy bằng `node --test` với lớp tương thích `describe/it/expect` | 16/16 PASS |
| Giao diện | Bundle esbuild + Tailwind v4 (`compile` của gói `tailwindcss`), phục vụ cùng API public giả lập: SSE meta/delta/complete, conversations/messages, documents 200/404; nguyên văn Điều 17 lấy từ `data/doanh-nghiep/interim/luat-59-2020-qh14-v1.txt` | 17/17 ca × 2 khung hình PASS |

Bản build và API giả lập là công cụ kiểm tra tạm, không đưa vào repository. Chúng không thay `npm run build` thật.

## 2. Kịch bản trình duyệt

Chạy ở 1280×860 và 360×760 (Chromium headless). Không có lỗi JavaScript; lỗi console duy nhất là phản hồi 404 cố ý của ca nguồn bị gỡ.

| # | Kịch bản | Kết quả |
| --- | --- | --- |
| B01 | Màn hình chào hiện "Phạm vi dữ liệu", bản dữ liệu "Chưa công bố", chế độ thử nghiệm | PASS |
| B02 | Câu trả lời có tiêu đề, gạch đầu dòng, dòng dẫn + danh sách 1./2., 3 thẻ căn cứ | PASS |
| B03 | Thẻ C1 ghi "Điều 17, Khoản 2, Điểm b", có link "Nguồn chính thức" HTTPS | PASS |
| B04 | Mở C1 bằng bàn phím (Enter trên marker): tô sáng đúng "b) Cán bộ, công chức, viên chức…", không lấn sang điểm c | PASS |
| B05 | Marker và thẻ C1 được đánh dấu đang mở | PASS |
| B06 | Focus vào ngăn, 6 lần Tab vẫn trong ngăn, Escape đóng và trả focus về marker | PASS |
| B07 | Mở C3 từ thẻ: tô sáng toàn Khoản 3 | PASS |
| B08 | "Mở trang riêng" → `/documents/luat-59-2020-qh14-v1?articleId=dieu-17&clause=…&cite=C3`, tải lại vẫn tô sáng | PASS |
| B09 | Citation tới Điều không còn (404): thông báo, nút mở nguồn chính thức của citation, câu trả lời vẫn hiển thị | PASS |
| B10 | `insufficient_context`: không có thẻ căn cứ hay marker | PASS |
| B11 | Không cuộn ngang ở 360px | PASS |

Unit test bao phủ thêm: điểm `đ)`, khoản cuối Điều, Điều chỉ có điểm, số trong câu không bị nhận nhầm là đầu khoản,
nhãn lạ/không tồn tại/trùng vị trí trả về "không tô", ký tự HTML giữ nguyên dạng văn bản, CRLF.

## 3. Chạy lại trên máy Windows của nhóm

Ngày 24/10/2026, từ `team3_fullstack/frontend`, npm 10.9.3, commit `e315550`:

| Lệnh | Kết quả |
| --- | --- |
| `npm test` | Vitest 2.1.9: 7 file, **72/72 PASS** (56 test cũ + 16 test mới) |
| `npm run build` | `tsc -b` + Vite 5.4.21: PASS, 78 modules; CSS 36.89 kB, JS 231.95 kB |

Còn lại:

Smoke VLRA-42 (Edge/CDP, Java profile `rag`, PostgreSQL test riêng) theo
[quickstart VLRA-42](../002-vlra-42-fe-be-integration/quickstart.md): ca B09 của VLRA-42 đã đổi nội dung chờ
sang "Không mở được nguyên văn" và kiểm thêm link nguồn dự phòng.

## 4. Giới hạn

- Tô sáng dựa trên định dạng corpus hiện tại (`N. ` cho khoản, `a) ` cho điểm). Văn bản có cấu trúc khác sẽ không được tô
  và hiển thị lời nhắc đối chiếu toàn Điều.
- Viewer thật cần Team 2 bổ sung `GET /internal/v1/documents/{document_id}/articles/{article_id}`; nhánh
  `feature/team2/datdo-week4` hiện chỉ có `/internal/v1/query`, `/health`, `/ready`.
- Chưa có API công bố snapshot; `VITE_CORPUS_SNAPSHOT` phải được điền khi phát hành bản dữ liệu.
- Bản xem trước không tải font Be Vietnam Pro/Noto Serif từ Google Fonts; giao diện thật dùng font của dự án.
