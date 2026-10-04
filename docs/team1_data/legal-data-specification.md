# Legal Data Specification

## 1. Mục tiêu

Xác định phạm vi, nguồn, định dạng và cấu trúc dữ liệu pháp luật được sử dụng
cho hệ thống Vietnamese Legal RAG Assistant. Tài liệu này là đầu vào cho
[Data Processing Flow](data-processing-flow.md), [Chunk Format](chunk-format-spec.md)
và [Metadata Specification](metadata-specification.md).

## 2. Phạm vi dữ liệu

Giai đoạn đầu tập trung vào **pháp luật lao động**: Bộ luật Lao động 2019, các
luật sửa đổi và các văn bản hướng dẫn còn hiệu lực. Phạm vi này thống nhất với
`contracts/v0.1/README.md` của Team 2.

Chọn lĩnh vực lao động vì câu hỏi thực tế đa dạng và gần người dùng hơn (nghỉ
phép, làm thêm giờ, thử việc, sa thải, trợ cấp thôi việc), nên bộ câu hỏi đánh
giá retrieval dễ xây dựng và sát thực tế.

### 2.1. Danh mục văn bản

Mức ưu tiên: **P0** bắt buộc cho MVP, **P1** nên có, **P2** bổ sung sau.

| Ưu tiên | Số hiệu | Loại | Cơ quan ban hành | Trích yếu | Ngày ban hành | Ngày hiệu lực | Ghi chú |
|---|---|---|---|---|---|---|---|
| P0 | 45/2019/QH14 | Bộ luật | Quốc hội | Bộ luật Lao động | 20/11/2019 | 01/01/2021 | Văn bản gốc; 17 chương, 220 điều. Đã được sửa đổi bởi 71/2025/QH15 |
| P0 | 125/VBHN-VPQH | Văn bản hợp nhất | Văn phòng Quốc hội | Hợp nhất Bộ luật Lao động | 2025 | — | **Nguồn nội dung tra cứu chính** (xem mục 4.3) |
| P0 | 145/2020/NĐ-CP | Nghị định | Chính phủ | Hướng dẫn Bộ luật Lao động về điều kiện lao động và quan hệ lao động | 14/12/2020 | 01/02/2021 | Hết hiệu lực một phần; đã sửa bởi NĐ 35/2022/NĐ-CP và NĐ 129/2025/NĐ-CP |
| P0 | 293/2025/NĐ-CP | Nghị định | Chính phủ | Mức lương tối thiểu đối với người lao động làm việc theo hợp đồng lao động | 10/11/2025 | 01/01/2026 | Thay thế NĐ 74/2024/NĐ-CP |
| P0 | 135/2020/NĐ-CP | Nghị định | Chính phủ | Quy định về tuổi nghỉ hưu | 18/11/2020 | 01/01/2021 | Còn hiệu lực |
| P1 | 71/2025/QH15 | Luật | Quốc hội | Luật Công nghiệp công nghệ số (có sửa đổi Bộ luật Lao động) | 14/06/2025 | 01/01/2026 | Chỉ lấy phần sửa đổi Bộ luật Lao động |
| P1 | 219/2025/NĐ-CP | Nghị định | Chính phủ | Người lao động nước ngoài làm việc tại Việt Nam | 07/08/2025 | 07/08/2025 | Thay thế nội dung tương ứng của NĐ 152/2020 và NĐ 70/2023 |
| P1 | 12/2022/NĐ-CP | Nghị định | Chính phủ | Xử phạt vi phạm hành chính trong lĩnh vực lao động, BHXH | 17/01/2022 | 17/01/2022 | Hữu ích cho câu hỏi về chế tài |
| P2 | 10/2020/TT-BLĐTBXH | Thông tư | Bộ LĐ-TB&XH | Hướng dẫn một số nội dung về hợp đồng lao động, kỷ luật lao động | 12/11/2020 | 01/01/2021 | Kiểm tra trạng thái sau khi sắp xếp lại bộ máy năm 2025 |

**Không đưa vào index mặc định** (đã hết hiệu lực, chỉ lưu raw để đối chiếu):
NĐ 74/2024/NĐ-CP, NĐ 152/2020/NĐ-CP, NĐ 70/2023/NĐ-CP.

Mọi thông tin ngày và trạng thái trong bảng phải được kiểm tra lại trên nguồn
chính thức (mục 3.1) tại thời điểm thu thập và ghi vào registry văn bản (mục 5).

### 2.2. Nguyên tắc lựa chọn văn bản

- Chỉ đưa vào index mặc định văn bản **còn hiệu lực** hoặc **còn hiệu lực một phần**.
- Văn bản hết hiệu lực không bị xóa khỏi raw storage; nếu sau này cần hỏi về
  quy định cũ thì index với `legal_status = het_hieu_luc` và lọc mặc định.
- Ưu tiên văn bản hợp nhất cho nội dung tra cứu; giữ văn bản sửa đổi riêng để
  trích dẫn đúng căn cứ (mục 4.3).
- Mọi văn bản phải có nguồn chính thức để truy xuất lại và kiểm chứng.

## 3. Nguồn và định dạng dữ liệu

### 3.1. Nguồn thu thập

| Thứ tự ưu tiên | Nguồn | Định dạng cung cấp | Vai trò |
|---|---|---|---|
| 1 | Cơ sở dữ liệu quốc gia về VBPL — `vbpl.vn` (Bộ Tư pháp) | HTML, file đính kèm DOC/PDF | Nguồn chính; có thuộc tính hiệu lực và quan hệ văn bản |
| 2 | Công báo Chính phủ — `congbao.chinhphu.vn` | PDF, DOC | Bản chính thức để đối chiếu nội dung và ngày ban hành |
| 3 | Thư viện Pháp luật, LuatVietnam | HTML | Chỉ tham khảo thủ công để kiểm tra trạng thái; không crawl tự động do điều khoản sử dụng |

`source_url` trong metadata phải là URL HTTPS tới nguồn 1 hoặc 2.

### 3.2. Định dạng nguồn và cách xử lý

| Định dạng | Ưu tiên | Ưu điểm | Rủi ro | Công cụ đề xuất |
|---|---|---|---|---|
| HTML | 1 | Giữ cấu trúc đoạn, không cần OCR, dễ tách Điều/Khoản | Lẫn menu, quảng cáo, script; cấu trúc DOM khác nhau giữa các trang | `beautifulsoup4` + `lxml`, selector riêng cho từng nguồn |
| DOC / DOCX | 2 | Text sạch, giữ xuống dòng và in đậm tiêu đề | Công báo dùng `.doc` cũ; bảng biểu và phụ lục phức tạp | Chuyển `.doc` → `.docx` bằng LibreOffice headless, đọc bằng `python-docx` |
| PDF có text layer | 3 | Bản chính thức, bố cục cố định | Ngắt dòng giữa câu, header/footer, số trang, lỗi font tiếng Việt | `PyMuPDF` (fitz) hoặc `pdfplumber` |
| PDF scan | Tránh | — | Cần OCR, sai chữ, sai dấu | Chỉ dùng khi không có định dạng khác; OCR bằng Tesseract `vie`, bắt buộc kiểm tra thủ công |

Quy tắc: với mỗi văn bản, lấy **định dạng ưu tiên cao nhất có sẵn**; định dạng
khác (nếu có) được lưu kèm để đối chiếu khi validation.

### 3.3. Lưu trữ raw

```text
data/
├── raw/{document_id}/            # file gốc tải về theo phiên bản, không chỉnh sửa
│   ├── source.html | source.docx | source.pdf
│   └── fetch_info.json           # source_url, thời điểm tải, sha256, định dạng
├── interim/{document_id}.txt     # text sau cleaning, trước chunking
├── processed/chunks.jsonl        # chunk + metadata, đầu vào indexing
└── registry/documents.json       # registry văn bản (mục 5)
```

`sha256` của file raw dùng để phát hiện nguồn thay đổi và quyết định có cần
xử lý lại hay không.

## 4. Cấu trúc phân cấp văn bản

### 4.1. Các cấp

```text
Văn bản
└── Phần        (tùy chọn)  "Phần thứ nhất", "PHẦN I"
    └── Chương  (tùy chọn)  "Chương I", "CHƯƠNG II"
        └── Mục (tùy chọn)  "Mục 1", "MỤC 2"
            └── Điều        "Điều 113. Nghỉ hằng năm"
                └── Khoản   "1.", "2." ở đầu dòng
                    └── Điểm "a)", "b)", "đ)"
```

- **Điều** là cấp bắt buộc và là đơn vị trích dẫn chính.
- Phần, Chương, Mục có thể không tồn tại; khi không có thì metadata để `null`.
- Ví dụ: Bộ luật Lao động 2019 có 17 chương, 220 điều. Điều 113 nằm trong
  Chương VII (Thời giờ làm việc, thời giờ nghỉ ngơi), Mục 2 (Thời giờ nghỉ ngơi)
  — một ví dụ có đủ cả cấp Chương và Mục.

### 4.2. Quy tắc nhận diện

| Cấp | Mẫu nhận diện (áp dụng sau chuẩn hóa) | Ghi chú |
|---|---|---|
| Phần | `^(PHẦN\|Phần)\s+(thứ\s+\w+\|[IVXLC]+)` | Hiếm gặp trong phạm vi hiện tại |
| Chương | `^(CHƯƠNG\|Chương)\s+([IVXLC]+)` | Số La Mã; dòng kế tiếp thường là tên chương viết hoa |
| Mục | `^(MỤC\|Mục)\s+(\d+)` | Chỉ nhận diện khi nằm giữa Chương và Điều |
| Điều | `^Điều\s+(\d+[a-z]?)\.\s*(.*)` | `113a` xuất hiện khi luật sửa đổi bổ sung điều mới |
| Khoản | `^(\d+[a-z]?)\.\s+` | Chỉ tính khi đang ở trong một Điều |
| Điểm | `^([a-zđ])\)\s+` | Bảng chữ cái pháp lý: a b c d đ e g h i k l m n o p q r s t u v x y (không có f, j, w, z) |

Cần phân biệt "Điều 113." ở đầu dòng (tiêu đề điều) với "quy định tại khoản 3
Điều 101 của Bộ luật này" trong câu (tham chiếu chéo). Chỉ mẫu ở **đầu dòng**
mới mở một đơn vị mới.

> **Cảnh báo từ khảo sát nguồn:** bản hợp nhất Bộ luật Lao động lấy từ một số
> trang tổng hợp **bị mất hoàn toàn dòng tiêu đề Chương và phần lớn tiêu đề Mục**,
> chỉ còn lại các dòng `Điều N.`. Vì vậy bước Structure Extraction không được
> giả định luôn có Chương/Mục; khi thiếu thì `chapter`/`section` để `null` và
> ghi cảnh báo vào báo cáo xử lý. Ưu tiên nguồn `vbpl.vn` hoặc Công báo vì giữ
> đủ cấu trúc.

### 4.3. Văn bản sửa đổi và văn bản hợp nhất

Văn bản sửa đổi có cấu trúc lồng nhau, ví dụ:

```text
Điều 72. Sửa đổi, bổ sung một số điều của các luật có liên quan
1. Sửa đổi, bổ sung khoản 1 Điều 24 của Bộ luật Lao động như sau:
   "1. ..."
```

Nếu chunk trực tiếp, "khoản 1 Điều 24" của Bộ luật Lao động sẽ bị gán nhầm
thành "khoản 1 Điều 72" của luật sửa đổi. Vì vậy:

- **Nội dung tra cứu chính** lấy từ văn bản hợp nhất (VBHN) mới nhất, nơi các
  sửa đổi đã được ghép vào đúng Điều/Khoản gốc.
- **Văn bản sửa đổi** vẫn được index riêng, giữ nguyên cấu trúc của chính nó,
  và ghi quan hệ `amends` trong registry để Team 2 trích dẫn căn cứ sửa đổi.
- Nếu chưa có VBHN cập nhật sửa đổi mới nhất, đánh dấu các Điều bị ảnh hưởng
  bằng `amended_by` trong metadata để Team 2 cảnh báo khi trả lời.

### 4.4. Phần không phải nội dung quy phạm

| Thành phần | Xử lý |
|---|---|
| Quốc hiệu, tiêu ngữ, số hiệu, ngày ban hành ở đầu văn bản | Không chunk; trích xuất vào metadata văn bản |
| Phần "Căn cứ ..." | Không chunk; lưu vào registry (`legal_basis`) |
| Nơi nhận, chữ ký, chức danh | Loại bỏ |
| Phụ lục, biểu mẫu | Tách thành document con `{document_id}-pl{n}`; P2, chưa xử lý ở MVP |
| Bảng trong thân Điều | Giữ dạng text theo hàng, phân tách cột bằng ` \| ` |

## 5. Registry văn bản

Mỗi văn bản có một bản ghi trong `data/registry/documents.json`. Đây là nguồn
dữ liệu cấp văn bản; metadata cấp chunk được sao chép từ đây
(xem [Metadata Specification](metadata-specification.md)).

```json
{
  "document_key": "bl-45-2019-qh14",
  "document_id": "bl-45-2019-qh14-v1",
  "document_number": "45/2019/QH14",
  "document_type": "bo_luat",
  "document_title": "Bộ luật Lao động",
  "issuing_authority": "Quốc hội",
  "issued_date": "2019-11-20",
  "effective_date": "2021-01-01",
  "expiry_date": null,
  "legal_status": "con_hieu_luc",
  "amended_by": ["luat-71-2025-qh15"],
  "replaces": ["bl-10-2012-qh13"],
  "replaced_by": [],
  "guided_by": ["nd-145-2020-nd-cp", "nd-135-2020-nd-cp", "nd-293-2025-nd-cp"],
  "source_url": "https://vbpl.vn/...",
  "source_format": "html",
  "version": "v1",
  "fetched_at": "2026-10-04T00:00:00Z"
}
```

- `document_key` cố định cho một văn bản, dùng trong các quan hệ
  (`amended_by`, `guided_by`, ...).
- `document_id` = `{document_key}-{version}`, định danh một **phiên bản nội dung**;
  đây là ID xuất hiện trong chunk, citation và URL xem điều luật.

Registry được cập nhật khi có văn bản mới, văn bản bị sửa đổi hoặc thay đổi
trạng thái hiệu lực. Khi nội dung văn bản thay đổi, tăng `version` và sinh
`document_id` mới; không tái sử dụng `document_id` cũ cho nội dung khác để
citation đã lưu vẫn trỏ đúng nội dung.
