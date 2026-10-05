# Team 2 — Week 2 skeleton và mock

VLRA19 + VLRA21, phần Người 1. Module hiện luôn trả dữ liệu giả lập, không gọi
retrieval/LLM, không cần API key và không dùng văn bản pháp luật thật.

## Cài đặt trên macOS/Linux

Chạy từ thư mục gốc repo, Python 3.10 trở lên:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[rag,test]'
python -m team2_rag
python -m team2_rag --scenario insufficient_context
python -m unittest discover -s tests -p 'test_team2_*.py' -v
```

`rag` cài LangChain Core và python-dotenv làm nền cho Người 2; `test` cài
jsonschema cùng bộ kiểm tra format. Không cài thêm LlamaIndex, model local hay
SDK provider trong phần này. Có thể cài `-e '.[test]'` để chỉ chạy mock/test.
Mock không đọc `.env`. `.env.example` hiện có vẫn dành cho phần cấu hình
Người 2; người đó bổ sung provider/model/API key và hướng dẫn khi làm VLRA20.

## Team 3 tích hợp

```python
from team2_rag import query

response = query(question="Câu hỏi kiểm thử", history=[])
missing = query("Câu hỏi kiểm thử", [], scenario="insufficient_context")
```

Response chỉ có `status`, `answer`, `citations`, theo
[`contracts/v0.1/rag_response.schema.json`](../contracts/v0.1/rag_response.schema.json).
Test đọc trực tiếp schema chung, không dùng schema nháp trong docs Team 2.
`answered` có citation C1 và marker `[C1]`; `insufficient_context` không có citation.
Citation trỏ tới `https://example.com/mock-law`, không phải tài liệu thật.

`scenario` chỉ chọn fixture trong Python/CLI, không thêm field vào request API.
History được nhận để tương thích interface nhưng chưa được xử lý trong mock.
Team 3 kiểm tra payload đầy đủ, xử lý HTTP/error envelope và thêm ID/timestamp
vào public response theo docs của họ. Module này không dựng endpoint FastAPI.
Document Viewer chưa thể tải nguồn thật bằng ID giả lập này; Team 3 cần fixture
viewer riêng hoặc hiển thị trạng thái mock.

## Phân công đã chốt

| Người 1 | Người 2 |
| --- | --- |
| Khung module, package/môi trường, hướng dẫn | System Prompt, Context Injection Template |
| `mock.py`, `service.py` bản mock, test schema | API key/model, client và hàm gọi LLM thật |

`clients/` chừa sẵn cho Người 2. Người 2 tự bổ sung SDK của provider đã chọn
vào extra `rag` và viết test riêng. Chưa có client giả được gọi là client thật.
Khi có phần AI, phối hợp cập nhật điểm gọi `query(question, history)`; output cuối
vẫn theo contract chung. Context/retrieval nội bộ không thêm vào payload Team 3.
Phạm vi toàn bộ dự án là pháp luật lao động; corpus ưu tiên Bộ luật Lao động 2019 và các văn bản liên quan.