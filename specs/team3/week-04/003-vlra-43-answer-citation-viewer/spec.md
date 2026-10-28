# VLRA-43 — UI câu trả lời, căn cứ pháp lý và Legal Document Viewer

**Ngày:** 24/10/2026. **Nhánh:** `feature/team3/haunx`, nền `ac2d399` (VLRA-41/42).
**Jira:** [VLRA-43](https://banhvanhiep.atlassian.net/browse/VLRA-43), tuần 4, EPIC 4 Fullstack.

## Nguồn yêu cầu

- [Docs v2.0](https://docs.google.com/document/d/1uDCSGNfzWXIaCSdggRrxcSuRREJ3StS278r4vZWNYPM/edit?tab=t.0):
  §2.5 hình thức câu trả lời, §8.6 màn hình (Citation list, Document Viewer, Scope information),
  §8.7 UI state và render an toàn, §9.9 citation 9 trường, §9.11–9.12 Viewer/ArticleResponse, NFR-16.
- Phân chia công việc 9 tuần: tuần 4 "UI hiển thị Answer + Citation", tuần 7 "Viewer theo citation,
  loading/error/retry, responsive".
- [team3.md §2.4](../../../../docs/team3_fullstack/team3.md): lấy ID từ citation, được nhấn mạnh khoản/điểm khi xác định
  đúng vị trí; 404 vẫn cung cấp `source_url` của citation và giữ câu trả lời.
- Kế thừa VLRA-42: transport SSE, adapter public→view model, proxy Viewer. Không đổi API, contract hay phần Team 1/2.

## Yêu cầu chức năng

- **FR-01** Câu trả lời render an toàn từ văn bản: đoạn, tiêu đề, danh sách `- `/`1. `/`a) `, chữ đậm, `[Cn]`.
  Không dùng HTML từ LLM. `[Cn]` chỉ mở citation có trong array đã kiểm tra.
- **FR-02** Thẻ căn cứ hiển thị Cn, "Điều, Khoản, Điểm", tên văn bản, mở nguyên văn và link nguồn `sourceUrl`.
- **FR-03** Marker và thẻ của căn cứ đang mở được đánh dấu, chỉ trong tin nhắn chứa căn cứ đó.
- **FR-04** Viewer: tiêu đề văn bản, Điều, nguyên văn giữ xuống dòng, nguồn chính thức; loading/error có Thử lại.
- **FR-05** Viewer tô sáng khoản/điểm được trích khi nhãn chuẩn và vị trí duy nhất; nếu không chắc chắn thì báo người dùng
  đối chiếu toàn Điều, không tô đoán.
- **FR-06** 404 nguồn: báo không mở được nguyên văn, giữ câu trả lời, cho mở `sourceUrl` của citation.
- **FR-07** Ngăn xem là modal truy cập được bằng bàn phím: focus vào ngăn, giữ focus bên trong, Escape đóng và trả focus.
- **FR-08** Trang riêng `/documents/:documentId?articleId=…` nhận thêm `clause`, `point`, `cite` để tô sáng khi mở lại
  hoặc chia sẻ. Ba tham số này không dùng để tra cứu.
- **FR-09** "Phạm vi dữ liệu": lĩnh vực, bản dữ liệu, chế độ thử nghiệm/thật, không tuyên bố đã có mọi luật.
- **FR-10** Sao chép câu trả lời kèm danh sách căn cứ và nguồn.
- **FR-11** Dùng được từ 360px, không cuộn ngang.

## Ngoài phạm vi

API Search, đổi contract/endpoint, Python service, kiểm chứng nội dung pháp lý, E2E với RAG thật (VLRA-44),
thống nhất mã lỗi Python/Java (VLRA-47).

## Quyết định

- Vị trí khoản/điểm dựa trên dòng bắt đầu bằng `N. ` hoặc `a) ` trong nguyên văn, đúng định dạng corpus
  `data/doanh-nghiep` (nhãn `Khoản N`, `Điểm a`, có cả `đ`). Không phân tích tên Điều để tạo ID.
- Bản dữ liệu chưa có API công bố snapshot, nên lấy từ biến build `VITE_CORPUS_SNAPSHOT`; để trống hiển thị "Chưa công bố".
