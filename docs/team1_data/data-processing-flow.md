# Data Processing Flow

## 1. Mục tiêu

Xây dựng quy trình xử lý dữ liệu pháp luật từ văn bản gốc thành các chunk có
cấu trúc và metadata thống nhất, phục vụ BM25 Retrieval và Dense Retrieval.

Nguyên tắc xuyên suốt: **không làm thay đổi nội dung pháp lý**. Cleaning chỉ
loại bỏ thứ không thuộc văn bản (rác định dạng, ký tự lỗi, header trang) và
chuẩn hóa biểu diễn ký tự; không sửa chính tả, không diễn đạt lại câu chữ.

## 2. Tổng quan quy trình

```text
Registry văn bản (documents.json)
      ↓
[1] Collection          → data/raw/{document_id}/
      ↓
[2] Extraction          → text thô theo dòng
      ↓
[3] Cleaning & Normalization
      ↓
[4] Structure Extraction → cây Chương/Mục/Điều/Khoản/Điểm
      ↓                    data/interim/{document_id}.json
[5] Chunking            (Chunk Format Specification)
      ↓
[6] ID Generation       (Metadata Specification)
      ↓
[7] Metadata Enrichment (sao chép từ registry)
      ↓
[8] Validation          → processing_report.json
      ↓
data/processed/chunks.jsonl
      ↓
Indexing BM25 + Dense   (Retrieval Design)
```

Mỗi bước đọc output của bước trước từ đĩa, để có thể chạy lại một bước mà
không phải tải lại dữ liệu.

## 3. Các bước xử lý

### 3.1. Collection

- Đọc danh sách văn bản cần thu thập từ registry
  (xem [Legal Data Specification](legal-data-specification.md) mục 5).
- Tải file theo thứ tự ưu tiên định dạng: HTML → DOCX/DOC → PDF.
- Ghi `fetch_info.json`: `source_url`, `fetched_at`, `source_format`, `sha256`.
- Nếu `sha256` trùng lần tải trước thì bỏ qua các bước sau cho văn bản đó.
- Giới hạn tốc độ tải (tối thiểu 1 giây giữa hai request tới cùng domain),
  retry tối đa 3 lần với lỗi mạng tạm thời.

### 3.2. Extraction theo định dạng

| Định dạng | Cách lấy text | Lưu ý |
|---|---|---|
| HTML | Chọn vùng nội dung văn bản theo selector riêng từng nguồn; bỏ `script`, `style`, `nav`, `header`, `footer` | Giữ ranh giới đoạn (`p`, `br`, `div`) thành xuống dòng |
| DOCX | Đọc lần lượt paragraph và table bằng `python-docx` | `.doc` cũ chuyển sang `.docx` bằng LibreOffice headless trước |
| PDF | Đọc theo trang bằng `PyMuPDF`, giữ thứ tự dòng | Ghi số trang của từng dòng để bước 3.3 phát hiện header/footer |

Output: danh sách dòng text (kèm số trang với PDF).

### 3.3. Cleaning & Normalization

Các quy tắc chạy **theo đúng thứ tự** dưới đây.

| # | Quy tắc | Cách làm | Lý do |
|---|---|---|---|
| C1 | Sửa lỗi mã hóa (mojibake) | `ftfy.fix_text()`; phát hiện văn bản mã TCVN3/VNI (ví dụ `Ph¸p luËt`) và chuyển sang Unicode, nếu không chuyển được thì đánh lỗi văn bản | Văn bản cũ hoặc PDF lỗi font cho ra chữ không đọc được |
| C2 | Chuẩn hóa Unicode NFC | `unicodedata.normalize("NFC", text)` | PDF/DOCX hay dùng dấu tổ hợp (`a` + dấu sắc rời), làm cùng một chữ có hai biểu diễn khác nhau, BM25 và so khớp chuỗi sẽ sai |
| C3 | Xóa ký tự vô hình | Xóa U+200B (zero-width space), U+FEFF (BOM), U+00AD (soft hyphen), ký tự điều khiển trừ `\n`; đổi U+00A0 (non-breaking space) và `\t` thành dấu cách | Ký tự không nhìn thấy nhưng làm tách từ sai |
| C4 | Chuẩn hóa dấu câu | `“ ” „` → `"`; `‘ ’` → `'`; `– —` → `-`; `…` → `...` | Thống nhất biểu diễn, không đổi nghĩa |
| C5 | Bỏ header/footer trang (PDF) | Dòng xuất hiện ở đầu/cuối trang trên ≥ 50% số trang; dòng chỉ chứa số trang (`^\s*\d+\s*$`, `^Trang \d+`) | Header lặp lại chen giữa nội dung Điều |
| C6 | Nối dòng bị ngắt | Nối dòng hiện tại vào dòng trước nếu dòng trước không kết thúc bằng `. : ; ! ?` **và** dòng hiện tại không bắt đầu bằng mẫu cấu trúc (Chương/Mục/Điều/Khoản/Điểm, xem Legal Data Specification mục 4.2) | PDF ngắt dòng theo bố cục trang, cắt đôi câu |
| C7 | Bỏ rác web | Xóa dòng khớp danh sách mẫu theo nguồn: "Tải về", "In văn bản", "Văn bản liên quan", "Lược đồ", breadcrumb, quảng cáo | Chỉ áp dụng với HTML |
| C8 | Tách chú thích VBHN | Văn bản hợp nhất dùng chú thích `[1]`, `[2]` để ghi văn bản sửa đổi; chuyển nội dung chú thích vào metadata `amendment_notes` của Điều tương ứng và xóa marker khỏi content | Giữ thông tin căn cứ sửa đổi nhưng không làm bẩn text tìm kiếm |
| C9 | Bỏ phần không quy phạm | Cắt phần đầu văn bản trước Chương/Điều đầu tiên (quốc hiệu, căn cứ) và phần từ "Nơi nhận:" trở đi; thông tin cần giữ được trích vào registry trước khi cắt | Xem Legal Data Specification mục 4.4 |
| C10 | Chuẩn hóa khoảng trắng | Gộp nhiều dấu cách thành một; strip hai đầu dòng; tối đa một dòng trống liên tiếp | Bước cuối, dọn dẹp sau các bước trên |

**Không làm** trong bước này:

- Không lowercase, không bỏ dấu, không bỏ stopword trong `content`.
- Không đổi kiểu đặt dấu thanh (`hoà` / `hòa`, `thuỷ` / `thủy`) trong `content`.
  Việc chuẩn hóa này chỉ làm trên **text tìm kiếm** ở bước indexing
  (xem [BM25 Proposal](bm25-proposal.md)), để `content` hiển thị và trích dẫn
  vẫn đúng nguyên văn.
- Không tự sửa lỗi chính tả trong văn bản gốc.

### 3.4. Structure Extraction

Duyệt text từng dòng bằng một máy trạng thái (state machine):

```text
Dòng khớp "Chương ..."  → mở Chương mới, đóng Mục/Điều/Khoản/Điểm hiện tại
Dòng khớp "Mục ..."     → mở Mục mới trong Chương hiện tại
Dòng khớp "Điều N. ..." → mở Điều mới; phần sau dấu chấm là tên Điều
Dòng khớp "N. ..."      → mở Khoản mới (chỉ khi đang ở trong một Điều)
Dòng khớp "a) ..."      → mở Điểm mới (chỉ khi đang ở trong một Khoản)
Dòng khác               → nối vào đơn vị đang mở
```

- Chỉ dòng **bắt đầu** bằng mẫu mới mở đơn vị mới; "theo quy định tại khoản 3
  Điều 101 của Bộ luật này" giữa câu là tham chiếu, không phải tiêu đề.
- Điều không có Khoản: toàn bộ nội dung thuộc Điều.
- Phần text đứng trước Khoản 1 trong một Điều (câu dẫn) được lưu riêng là
  `article_intro` và gắn vào mọi chunk của Điều đó (xem Chunk Format).
- Output: `data/interim/{document_id}.json` dạng cây.

### 3.5. Chunking

Chia cây cấu trúc thành chunk theo [Chunk Format Specification](chunk-format-spec.md).

### 3.6. ID Generation

Sinh `document_id`, `article_id`, `chunk_id` theo quy tắc xác định (deterministic)
trong [Metadata Specification](metadata-specification.md) mục 4. Chạy lại pipeline
trên cùng phiên bản văn bản phải sinh ra đúng các ID cũ.

### 3.7. Metadata Enrichment

Sao chép metadata cấp văn bản (số hiệu, loại, cơ quan ban hành, ngày ban hành,
hiệu lực, `source_url`, ...) từ registry vào từng chunk. Chunk không tự suy ra
các trường này từ nội dung.

### 3.8. Validation

| Nhóm | Kiểm tra | Mức |
|---|---|---|
| Schema | Mỗi chunk hợp lệ theo `schemas/chunk_metadata.schema.json` | Lỗi — dừng |
| Duy nhất | `chunk_id` không trùng trong toàn bộ dataset | Lỗi — dừng |
| Nội dung | `content` không rỗng; độ dài trong giới hạn của Chunk Format | Lỗi — dừng |
| Cấu trúc | Số Điều liên tục 1..N (cho phép điều chèn như `17a`); số Khoản liên tục trong Điều; chữ cái Điểm đúng thứ tự | Cảnh báo |
| Đối chiếu | Số Điều trích xuất bằng số Điều kỳ vọng ghi trong registry (ví dụ Bộ luật Lao động 2019: 220) | Lỗi — dừng |
| Ký tự | Tỷ lệ ký tự ngoài bảng chữ tiếng Việt, số và dấu câu < 1% | Cảnh báo, nghi lỗi mã hóa |
| Nguồn | `source_url` là HTTPS và nằm trong danh sách domain nguồn chính thức | Lỗi — dừng |
| Thủ công | Lấy ngẫu nhiên 5% chunk (tối thiểu 20) so với văn bản gốc | Ghi vào báo cáo |

Kết quả ghi vào `data/processed/processing_report.json`: số văn bản, số Điều,
số chunk, danh sách cảnh báo và lỗi theo `document_id`.

## 4. Output

Mỗi dòng của `data/processed/chunks.jsonl` là một chunk với đầy đủ trường theo
[Metadata Specification](metadata-specification.md). Ví dụ rút gọn:

```json
{
  "chunk_id": "bl-45-2019-qh14-v1__dieu-113__k1__0",
  "document_id": "bl-45-2019-qh14-v1",
  "article_id": "dieu-113",
  "document_title": "Bộ luật Lao động",
  "document_number": "45/2019/QH14",
  "article": "Điều 113",
  "clause": "Khoản 1",
  "point": null,
  "content": "...",
  "source_url": "https://vbpl.vn/..."
}
```

## 5. Thư viện đề xuất

| Việc | Thư viện |
|---|---|
| Tải dữ liệu | `httpx` hoặc `requests` |
| Parse HTML | `beautifulsoup4`, `lxml` |
| Đọc DOCX | `python-docx`; LibreOffice headless để chuyển `.doc` |
| Đọc PDF | `PyMuPDF` (chính), `pdfplumber` (khi cần đọc bảng) |
| Sửa mã hóa | `ftfy` |
| Chuẩn hóa Unicode | `unicodedata` (thư viện chuẩn Python) |
| Validation schema | `jsonschema` |

## 6. Chạy lại và lỗi

- Pipeline idempotent: cùng file raw (cùng `sha256`) cho ra cùng chunk và ID.
- Văn bản lỗi ở bước nào thì dừng riêng văn bản đó, ghi lỗi vào báo cáo và
  tiếp tục văn bản khác; không xuất chunk của văn bản lỗi.
- Khi đổi quy tắc cleaning hoặc chunking, tăng `pipeline_version` trong báo cáo
  và chạy lại toàn bộ để index không lẫn chunk của hai phiên bản quy tắc.
