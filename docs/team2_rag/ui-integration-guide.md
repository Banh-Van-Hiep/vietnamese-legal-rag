# Hướng dẫn tích hợp giao diện với AI Service (VLRA-T2-32)

Tài liệu bàn giao của Team 2 cho Team 3. Nguồn chuẩn vẫn là `contracts/v0.1/` (JSON Schema). Tài liệu này lệch với
contract thì theo contract và báo Team 2.

## 1. Luồng dữ liệu

Frontend không gọi AI Service trực tiếp. Frontend gọi Backend (`POST /api/v1/chat/stream`), Backend gọi AI Service
(`POST /internal/v1/query`, header `X-Request-ID`) rồi đổi lỗi nội bộ thành mã công khai. Chi tiết ở
`docs/ARCHITECTURE.md` mục 3.

AI Service trả đúng ba trường `status`, `answer`, `citations` (xem `contracts/v0.1/rag_response.schema.json`):

- `status = "answered"`: `answer` có marker `[C1]`, `[C2]`... và `citations` có đúng các nhãn đó, đánh số liên tục
  theo thứ tự xuất hiện đầu tiên trong `answer`.
- `status = "insufficient_context"`: không đủ căn cứ. `citations = []` và `answer` không có marker. Đây không phải lỗi
  hệ thống, hiển thị như thông báo "Chưa đủ căn cứ".

## 2. Bảng mã lỗi

AI Service trả lỗi dạng `{"error": {"code", "message", "retryable"}}`, kèm header `X-Request-ID`. Cột "Backend trả
cho Frontend" lấy từ `HttpAiClient.java` (`team3_fullstack/backend/.../ai/HttpAiClient.java`).

### `POST /internal/v1/query`

| Mã nội bộ (wire code) | HTTP | `retryable` | Ý nghĩa | Backend trả cho Frontend |
| :--- | :---: | :---: | :--- | :--- |
| `INVALID_LLM_OUTPUT` | 502 | false | LLM trả JSON sai cấu trúc hoặc sai contract | 502 `UPSTREAM_INVALID_RESPONSE`, false |
| `CITATION_INVALID` | 502 | false | Citation không khớp context, hoặc bước Verification không qua | 502 `UPSTREAM_INVALID_RESPONSE`, false |
| `LLM_UNAVAILABLE` | 503 | true | LLM lỗi hoặc quá tải; AI Service đang xử lý request khác; cấu hình LLM thiếu | 503 `SERVICE_UNAVAILABLE`, true |
| `LLM_TIMEOUT` | 504 | true | LLM hoặc toàn pipeline quá thời gian (trần 45 giây) | 504 `UPSTREAM_TIMEOUT`, true |
| `RETRIEVAL_UNAVAILABLE` | 503 | true | Tìm kiếm (BM25, Qdrant) hoặc reranker không dùng được | 503 `SERVICE_UNAVAILABLE`, true |
| `RETRIEVAL_TIMEOUT` | 504 | true | Tìm kiếm quá thời gian (mặc định 10 giây) | 504 `UPSTREAM_TIMEOUT`, true |
| `INVALID_REQUEST` | 400 | false | Body sai: thiếu hoặc thừa khóa, câu hỏi rỗng hoặc quá 2000 ký tự | 502 `UPSTREAM_CONTRACT_ERROR`, false |
| `INTERNAL_ERROR` | 500 | false | Lỗi không phân loại được | 502 `UPSTREAM_ERROR`, false |

`INVALID_REQUEST` ở đây là lỗi giữa Backend và AI Service, không phải lỗi của người dùng: Backend phải chặn câu hỏi
sai trước khi gọi AI Service.

### `GET /internal/v1/documents/{document_id}/articles/{article_id}`

| Mã nội bộ | HTTP | `retryable` | Ý nghĩa | Backend trả cho Frontend |
| :--- | :---: | :---: | :--- | :--- |
| `DOCUMENT_NOT_FOUND` | 404 | false | Không có văn bản `document_id` | 404 `DOCUMENT_NOT_FOUND`, false |
| `ARTICLE_NOT_FOUND` | 404 | false | Văn bản có, nhưng không có Điều `article_id` | 404 `ARTICLE_NOT_FOUND`, false |
| `INVALID_REQUEST` | 400 | false | `document_id` hoặc `article_id` chứa ký tự không hợp lệ | 502 `UPSTREAM_CONTRACT_ERROR`, false |

Quy tắc chung cho giao diện: `retryable = true` thì cho nút "Thử lại"; `false` thì báo lỗi, không tự gửi lại.

## 3. Bắt marker `[Cn]` để mở Document Viewer

Marker hợp lệ chỉ có dạng `[C` + số nguyên dương không bắt đầu bằng 0 + `]`, ví dụ `[C1]`, `[C12]`. AI Service đã từ
chối mọi dạng khác (`[C0]`, `[C01]`, `[c1]`, `[ C1 ]`) trước khi trả, nên Frontend chỉ cần một regex:

```ts
const MARKER = /\[C([1-9][0-9]*)\]/g;

// Tách answer thành đoạn chữ và marker; marker chỉ thành link khi citation_id có trong danh sách citations.
function splitMarkers(answer: string, citationIds: Set<string>) {
  const parts: Array<{ text: string } | { citationId: string }> = [];
  let last = 0;
  for (const m of answer.matchAll(MARKER)) {
    const id = `C${m[1]}`;
    if (m.index > last) parts.push({ text: answer.slice(last, m.index) });
    parts.push(citationIds.has(id) ? { citationId: id } : { text: m[0] });
    last = m.index + m[0].length;
  }
  if (last < answer.length) parts.push({ text: answer.slice(last) });
  return parts;
}
```

Khi người dùng bấm `[Cn]`, lấy citation có `citationId` đó và mở Viewer bằng `documentId` + `articleId`; `clause`,
`point` chỉ dùng để tô sáng. Frontend hiện đã làm việc này ở `src/utils/answerFormat.ts` (`\[C\d+\]`). Regex trên chặt
hơn một chút (không nhận `[C0]`), nhưng với dữ liệu AI Service trả về thì hai cách cho cùng kết quả.

Không chèn `answer` thành HTML. Render bằng component để tránh XSS.

## 4. Markdown trong câu trả lời

Câu trả lời có thể có xuống dòng, danh sách `- `, `1. `, `a) `, chữ đậm `**...**`, tiêu đề, và đôi khi bảng `| ... |`.
AI Service giữ nguyên các ký tự này (đã có test `tests/test_team2_mock_markdown.py`). Marker có thể nằm trong ô
bảng, và thứ tự marker vẫn được kiểm tra như ở văn bản thường.

`answerFormat.ts` hiện chưa có kiểu `table`, nên bảng sẽ hiện thành các dòng chữ có dấu `|`. Prompt không yêu cầu LLM
dùng bảng nên trường hợp này hiếm, nhưng Team 3 nên quyết định hiển thị bảng hay giữ dạng chữ.

## 5. Kiểm thử bằng mock

Chạy AI Service giả lập (không cần model, index hay API key):

```bash
RAG_MOCK_SCENARIO=answered_markdown .venv/bin/python -m uvicorn team2_rag.api.mock_app:create_mock_app --factory --port 8001
```

| `RAG_MOCK_SCENARIO` | Kết quả |
| :--- | :--- |
| `answered` (mặc định) | 200, một citation `[C1]` |
| `answered_markdown` | 200, danh sách lồng nhau, bảng, chữ đậm, hai citation `[C1]`, `[C2]` |
| `insufficient_context` | 200, `citations = []` |
| `error_timeout` | 504 `LLM_TIMEOUT`, retryable true |
| `error_busy` | 503 `LLM_UNAVAILABLE`, retryable true |
| `error_invalid_output` | 502 `INVALID_LLM_OUTPUT`, retryable false |

Biến được đọc ở mỗi request. Lookup Điều giả lập: `GET /internal/v1/documents/mock_v1/articles/art1`; mã khác trả
404 `DOCUMENT_NOT_FOUND` hoặc `ARTICLE_NOT_FOUND`. Mọi phản hồi mock có header `X-RAG-Mode: mock`.
