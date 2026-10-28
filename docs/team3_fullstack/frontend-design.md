# Thiết kế Chat, Citation và Document Viewer

**Loại:** thiết kế chung Team 3. **Đối chiếu source:** `62c3556`, ngày 28/10/2026.
**Căn cứ:** [ARCHITECTURE](../ARCHITECTURE.md) §2.2/§3.1 và
[CODING_CONVENTIONS](../CODING_CONVENTIONS.md) §3.3.
Các wireframe dưới đây mô tả UI đang có trong source, **được đại diện Team 3 xác nhận
đã duyệt ngày 29/10/2026**. Xác nhận trực tiếp đủ cho hồ sơ; không yêu cầu nguồn hoặc
danh tính bổ sung. Đây là baseline hiện tại, không ngăn điều chỉnh UI cho phù hợp hơn.

## 1. Component và route

| Thành phần | Source và trách nhiệm |
| --- | --- |
| App/AppLayout |[Router](../../team3_fullstack/frontend/src/App.tsx), [layout](../../team3_fullstack/frontend/src/components/layout/AppLayout.tsx): sidebar + main |
| ChatPage/useChat |[ChatPage](../../team3_fullstack/frontend/src/pages/ChatPage.tsx), [useChat](../../team3_fullstack/frontend/src/hooks/useChat.ts): gửi/retry/meta binding/history |
| Sidebar/AppContext |[Sidebar](../../team3_fullstack/frontend/src/components/layout/Sidebar.tsx), [AppContext](../../team3_fullstack/frontend/src/context/AppContext.tsx): list/select/delete, loading/error và stale guard |
| ChatWindow/Input/MessageBubble |[ChatWindow](../../team3_fullstack/frontend/src/components/chat/ChatWindow.tsx), [ChatInput](../../team3_fullstack/frontend/src/components/chat/ChatInput.tsx), [MessageBubble](../../team3_fullstack/frontend/src/components/chat/MessageBubble.tsx): input và các nhánh thông báo |
| Citation/Answer |[CitationCard](../../team3_fullstack/frontend/src/components/citation/CitationCard.tsx), [AnswerContent](../../team3_fullstack/frontend/src/components/chat/AnswerContent.tsx): căn cứ và render an toàn |
| Viewer |[DocumentDrawer](../../team3_fullstack/frontend/src/components/document/DocumentDrawer.tsx), [DocumentViewer](../../team3_fullstack/frontend/src/components/document/DocumentViewer.tsx), [useArticle](../../team3_fullstack/frontend/src/hooks/useArticle.ts): nguồn nguyên văn/loading/error |

| Route FE | Hành vi |
| --- | --- |
| `/` |Câu hỏi mới; chưa gọi POST create conv trước câu đầu |
| `/c/:conversationId` |Tải history đã lưu, tiếp tục đúng conv số |
| `/documents/:documentId?articleId=...` |Viewer độc lập, hỗ trợ optional clause/point/cite để focus |
| `/documents/:documentId/articles/:articleId` |Alias FE đã có; không phải route public API mới |
| `/search` |Trang khung/fixture tìm kiếm, chưa là API Search thật |
| `/try-backend` |Công cụ JSON mock riêng, ngoài AppLayout/main chat SSE |

## 2. Wireframe desktop theo source

```text
+----------------------+--------------------------------------------------+
| Legal AI             | Tiêu đề hội thoại                         Menu   |
| [Câu hỏi mới]        +--------------------------------------------------+
|                      | Nhãn dữ liệu mock / thông tin phạm vi            |
| Hôm nay              |                                                  |
| - Tiêu đề câu đầu    |                         [Câu hỏi người dùng]     |
| - Hội thoại khác     |                                                  |
|                      | Assistant: nội dung trả lời                       |
| ... chọn / xóa ...   | [C1] -> [Thẻ căn cứ C1: văn bản, Điều/Khoản]      |
|                      |                                                  |
| Tra cứu văn bản      | [Dừng nhận] khi đang nhận / [Tải lại trạng thái]  |
|                      +--------------------------------------------------+
|                      | [Nhập câu hỏi ...                       Gửi]     |
|                      | Số ký tự / thông tin giới hạn                    |
+----------------------+--------------------------------------------------+
```

Sidebar rộng280px ở desktop. Nội dung Chat/input giới hạn khoảng760px ở giữa; trạng
thái mới có câu gợi ý và ScopeNote. Wireframe là bố cục chức năng, không thay CSS/token.
Các nhãn/câu trả lời minh họa không phải đáp án pháp lý.

### 2.1. Khi bấm citation

```text
+-------------------+--------------------+-------------------------------+
|                   | Chat bên dưới      | Nguyên văn điều luật   [X]    |
|  Sidebar          | được giữ lại       | [Mở trang riêng]              |
|                   |                    +-------------------------------+
|      Backdrop phủ toàn màn hình        | Tên văn bản                   |
|      Click backdrop hoặc Escape đóng   | Điều ... / Căn cứ C1          |
|                   |                    | Phần trích được tô sáng       |
|                   |                    | Toàn Điều, cuộn độc lập       |
|                   |                    | [Mở nguồn gốc HTTPS]          |
+-------------------+--------------------+-------------------------------+
```

Drawer là **modal overlay fixed bên phải**, rộng min(560px,100vw), không phải cột thứ ba
luôn chiếm chỗ và làm Chat reflow. Body Chat/answer không bị xóa khi mở/đóng/lỗi nguồn.
Nút đóng nhận focus; Tab/Shift+Tab giữ focus trong panel; Escape/backdrop đóng và trả
focus về phần tử đã mở. Có role dialog/aria-modal và link mở trang Viewer riêng.

## 3. Mobile và tablet

```text
+--------------------------------+
| [Menu] Tiêu đề hội thoại        |
+--------------------------------+
| Câu hỏi / câu trả lời           |
| [C1] [Thẻ căn cứ]               |
|                                |
+--------------------------------+
| [Nhập câu hỏi ...]       [Gửi]  |
+--------------------------------+

Mở nguồn trên màn hình 360px:
+--------------------------------+
| Nguyên văn điều luật       [X]  |
| [Mở trang riêng]                |
+--------------------------------+
| Điều và toàn văn (cuộn)         |
| [Mở nguồn gốc]                  |
+--------------------------------+
```

- Breakpoint≤860px: sidebar thành off-canvas với backdrop, rộng min(86vw,280px).
- Breakpoint≤600px: giảm padding/gap, câu gợi ý thành một cột.
- Drawer ở mobile có thể phủ toàn chiều rộng; ở tablet vẫn giới hạn560px.
- Các số trên lấy từ class Tailwind hiện tại, không là kích thước thiết kế mới tự đặt.

## 4. Trạng thái và tương tác

| Tình huống | Hiển thị / hành vi hiện tại |
| --- | --- |
| Chưa có conv |Câu gợi ý, phạm vi, ô nhập; gửi câu đầu mới nhận conv từ meta |
| Tải history |Loading; lỗi404 có nút bắt đầu mới, lỗi khác có retry |
| Đang gửi/nhận |Khóa gửi trùng; pending/indicator; delta tạm render như text |
| Completed answered |Complete thay buffer bằng answer/citation chuẩn; marker mở nguồn |
| Completed insufficient |Thông báo thiếu căn cứ riêng, không tạo thẻ citation giả |
| Failed đã rõ |Thông báo code/trace an toàn; nếu retryable và là lượt cuối thì retry với UUID mới |
| Mạng lỗi/dừng nhận, outcomeUnknown |Giữ UUID và receipt; retry/reconcile đúng lượt, không tự gửi lượt khác |
| History còn pending |Chặn gửi mới; có nút tải lại trạng thái, không query AI lại chỉ vì reload |
| Đổi conv khi request cũ về |Abort nhận và kiểm epoch/route, không gắn answer cũ vào lựa chọn mới |
| Xóa conv |Xác nhận xóa; server chặn pending409; không xóa corpus |

Ô nhập kiểm question sau trim,1–2000 Unicode code point. Public IDs vẫn number;
adapter đổi sang string/snake_case cho view model nội bộ và route, không đổi wire API.
Receipt unresolved lưu sessionStorage, xóa khi terminal; không lưu toàn history/API key.
Storage bị chặn: tab hiện tại có thể giữ in-memory receipt nhưng không bảo đảm phục hồi
UUID sau reload trước meta. `VITE_MOCK_MODE` chỉ là nhãn, không tạo câu trả lời mock.

## 5. Viewer và an toàn render

- IDs lấy từ citation, không đoán từ tên Điều. useArticle kiểm response IDs, abort/stale
  guard và khóa kết quả theo selection để tránh nháy nguồn cũ.
- Loading/error/404 tách trong vùng nguồn. 404 có thể dùng sourceUrl đã biết của citation
  để đối chiếu nguồn gốc; không thay phiên bản hoặc xóa answer đang xem.
- Nội dung Điều là text với whitespace-pre-wrap; highlight Khoản/Điểm chỉ khi
  `locateCitedUnit` xác định được đúng đoạn. Không chắc thì hiển thị toàn Điều và báo rõ.
- Link nguồn mở tab mới với noopener/noreferrer; URL do validator kiểm HTTPS/host.
- AnswerContent dùng parser cấu trúc giới hạn: heading/bold/list/paragraph/marker;
  render React nodes/text. Không dùng dangerouslySetInnerHTML hoặc hứa hỗ trợ toàn bộ Markdown.
- HTML model trả về được giữ như text, không chạy script. Nguồn/grounding phải được
  kiểm riêng; render an toàn không chứng minh câu trả lời đúng luật.

Source hỗ trợ: [answerFormat](../../team3_fullstack/frontend/src/utils/answerFormat.ts),
[legalCitation](../../team3_fullstack/frontend/src/utils/legalCitation.ts),
[publicApi adapter](../../team3_fullstack/frontend/src/api/publicApi.ts),
[SSE transport](../../team3_fullstack/frontend/src/api/chatStream.ts).

## 6. Giới hạn và trạng thái tài liệu

Chưa thấy debug latency badge hoặc kết quả profiling re-render trong code được đọc.
Viewer render nguyên văn text; nếu task yêu cầu Markdown thì phải đối chiếu trước khi
thêm renderer, không coi implementation text hiện tại là đã hỗ trợ Markdown đầy đủ.
Wireframe đã được xác nhận duyệt theo vai trò/ngày ở đầu tài liệu; khi UI thay đổi,
cập nhật phần thiết kế bị ảnh hưởng và kiểm chứng tương ứng. Việc duyệt wireframe
không tự xác nhận G1 hoặc các khoảng thiếu implementation khác đã hoàn tất.
Quyết định nghiệm thu và validate từng task được lưu trong hồ sơ tuần tương ứng.
