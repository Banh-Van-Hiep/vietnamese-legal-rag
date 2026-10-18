# Legal Data Specification

## 1. Mục tiêu

Xác định phạm vi, nguồn, định dạng và cấu trúc dữ liệu pháp luật được sử dụng
cho hệ thống Vietnamese Legal RAG Assistant. Tài liệu này là đầu vào cho
[Data Processing Flow](data-processing-flow.md), [Chunk Format](chunk-format-spec.md)
và [Metadata Specification](metadata-specification.md).

## 2. Phạm vi dữ liệu

Giai đoạn đầu tập trung vào **lĩnh vực doanh nghiệp**: Luật Doanh nghiệp, luật
sửa đổi, và các văn bản hướng dẫn, đăng ký, xử phạt liên quan còn hiệu lực. Phạm
vi này thống nhất với `contracts/v0.1/README.md` của Team 2.

Chọn lĩnh vực doanh nghiệp vì câu hỏi thực tế đa dạng và có nhóm người dùng rõ
ràng (thành lập doanh nghiệp, góp vốn và thời hạn góp vốn, chuyển nhượng phần vốn
góp, cơ cấu quản trị, thủ tục đăng ký doanh nghiệp, mức xử phạt vi phạm về đăng
ký), nên bộ câu hỏi đánh giá retrieval dễ xây dựng và sát thực tế.

### 2.1. Danh mục văn bản

Mức ưu tiên: **P0** bắt buộc cho MVP, **P1** nên có, **P2** bổ sung sau.

Corpus đã thu nằm ở `data/doanh-nghiep/`. Bảng dưới đây là bản đọc cho người;
nguồn dữ liệu chính thức là `data/doanh-nghiep/registry/documents.json` (metadata
cấp văn bản, sha256, số điều) và `data/doanh-nghiep/CATALOG.txt` (phạm vi đã cắt
của từng văn bản và các quy tắc làm sạch đã áp dụng). Khi hai nơi lệch nhau,
registry là đúng.

| Ưu tiên | Số hiệu | Loại | Cơ quan ban hành | Trích yếu | Ban hành | Hiệu lực | Trạng thái | Phạm vi đã thu |
|---|---|---|---|---|---|---|---|---|
| P0 | 67/VBHN-VPQH | Văn bản hợp nhất | Văn phòng Quốc hội | Hợp nhất Luật Doanh nghiệp | 15/08/2025 | — | Còn hiệu lực | **Nguồn nội dung tra cứu chính** (mục 4.3). Đã gộp Luật 59/2020, 03/2022/QH15 và 76/2025/QH15; chú thích hợp nhất [1]–[54] giữ ở cuối file |
| P0 | 59/2020/QH14 | Luật | Quốc hội | Luật Doanh nghiệp | 17/06/2020 | 01/01/2021 | Hết hiệu lực một phần | Văn bản gốc, 10 chương, Điều 1–218. Giữ để trích dẫn căn cứ gốc |
| P0 | 76/2025/QH15 | Luật | Quốc hội | Sửa đổi, bổ sung một số điều của Luật Doanh nghiệp | 17/06/2025 | 01/07/2025 | Còn hiệu lực | Index riêng để trích dẫn căn cứ sửa đổi (mục 4.3) |
| P0 | 168/2025/NĐ-CP | Nghị định | Chính phủ | Đăng ký doanh nghiệp | 30/06/2025 | 01/07/2025 | Còn hiệu lực | Điều 1–124. Thay thế NĐ 01/2021/NĐ-CP |
| P0 | 7566/VBHN-BKHĐT | Văn bản hợp nhất | Bộ Kế hoạch và Đầu tư | Hợp nhất Nghị định quy định chi tiết một số điều của Luật Doanh nghiệp | 18/09/2024 | 01/04/2021 | Hết hiệu lực một phần | Điều 1–35. Hợp nhất NĐ 47/2021/NĐ-CP với phần sửa của NĐ 16/2023/NĐ-CP; không gồm phụ lục biểu mẫu đã bãi bỏ |
| P1 | 122/2021/NĐ-CP | Nghị định | Chính phủ | Xử phạt vi phạm hành chính lĩnh vực kế hoạch và đầu tư | 28/12/2021 | 01/01/2022 | Hết hiệu lực một phần | **Chỉ phần đăng ký doanh nghiệp**: quy định chung và Điều 43–63. Không gồm đấu thầu, đầu tư công, PPP, hợp tác xã, quy hoạch |
| P1 | 288/2026/NĐ-CP | Nghị định | Chính phủ | Sửa đổi, bổ sung một số điều của NĐ 122/2021/NĐ-CP | 21/07/2026 | 21/07/2026 | Còn hiệu lực | Phần sửa các điều xử phạt về đăng ký doanh nghiệp |
| P2 | 68/2025/TT-BTC | Thông tư | Bộ Tài chính | Biểu mẫu dùng trong đăng ký doanh nghiệp, đăng ký hộ kinh doanh | 01/07/2025 | 01/07/2025 | Hết hiệu lực một phần | Chỉ phần quy phạm Điều 1–3; phụ lục biểu mẫu chưa xử lý. Đã bị TT 121/2026/TT-BTC sửa |

**Chưa thu, cân nhắc đợt sau:** Luật 03/2022/QH15 (nội dung đã nằm trong VBHN 67),
nhóm nghị định trái phiếu doanh nghiệp (153/2020, 65/2022, 08/2023, 200/2026),
NĐ 248/2025, NĐ 16/2023 bản đầy đủ, TT 121/2026/TT-BTC, phụ lục biểu mẫu của
TT 68/2025.

**Không đưa vào index mặc định** (đã bị thay thế hoặc hết hiệu lực, chỉ nêu để
đối chiếu): NĐ 01/2021/NĐ-CP, TT 01/2021/TT-BKHĐT, TT 02/2023/TT-BKHĐT.

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

Dữ liệu được tách theo **lĩnh vực** ở cấp ngoài cùng, để sau này thêm lĩnh vực
mới mà không trộn corpus:

```text
data/{domain}/                    # hiện có: doanh-nghiep
├── CATALOG.txt                   # danh mục đã thu, phạm vi đã cắt, quy tắc làm sạch
├── raw/{document_id}/            # file gốc tải về theo phiên bản, không chỉnh sửa
│   ├── source.txt                # hoặc source.html | source.docx | source.pdf
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
            └── Điều        "Điều 47. Góp vốn thành lập công ty và cấp giấy chứng nhận phần vốn góp"
                └── Khoản   "1.", "2." ở đầu dòng
                    └── Điểm "a)", "b)", "đ)"
```

- **Điều** là cấp bắt buộc và là đơn vị trích dẫn chính.
- Phần, Chương, Mục có thể không tồn tại; khi không có thì metadata để `null`.
- Ví dụ: Luật Doanh nghiệp 59/2020/QH14 có 10 chương, Điều 1–218. Điều 47 nằm
  trong Chương III (Công ty trách nhiệm hữu hạn), Mục 1 (Công ty trách nhiệm hữu
  hạn hai thành viên trở lên) — một ví dụ có đủ cả cấp Chương và Mục. Trong corpus
  hiện tại chỉ Luật 59/2020 và VBHN 67 (bù theo Luật 59/2020) có cấp Mục; xem
  cảnh báo ở mục 4.2.

### 4.2. Quy tắc nhận diện

| Cấp | Mẫu nhận diện (áp dụng sau chuẩn hóa) | Ghi chú |
|---|---|---|
| Phần | `^(PHẦN\|Phần)\s+(thứ\s+\w+\|[IVXLC]+)` | Hiếm gặp trong phạm vi hiện tại |
| Chương | `^(CHƯƠNG\|Chương)\s+([IVXLC]+)` | Số La Mã; dòng kế tiếp thường là tên chương viết hoa |
| Mục | `^(MỤC\|Mục)\s+(\d+)` | Chỉ nhận diện khi nằm giữa Chương và Điều |
| Điều | `^Điều\s+(\d+[a-z]?)\.\s*(.*)` | `47a` xuất hiện khi luật sửa đổi bổ sung điều mới |
| Khoản | `^(\d+[a-z]?)\.\s+` | Chỉ tính khi đang ở trong một Điều |
| Điểm | `^([a-zđ])\)\s+` | Bảng chữ cái pháp lý: a b c d đ e g h i k l m n o p q r s t u v x y (không có f, j, w, z) |

Cần phân biệt "Điều 47." ở đầu dòng (tiêu đề điều) với "quy định tại khoản 2
Điều 17 của Luật này" trong câu (tham chiếu chéo). Chỉ mẫu ở **đầu dòng** mới mở
một đơn vị mới.

> **Cảnh báo, đã xảy ra trên corpus hiện tại:** bản HTML của VBHN 67/VBHN-VPQH —
> chính là nguồn tra cứu chính ở mục 2.1 — **bị mất hoàn toàn dòng tiêu đề Chương
> và Mục**, chỉ còn các dòng `Điều N.`; `raw/vbhn-67-vbhn-vpqh-v1/source.txt` không
> có một dòng `Chương`/`Mục` nào. Vì VBHN 67 và Luật 59/2020 dùng cùng hệ thống số
> Điều (218 `article_id` khớp 1:1), `chapter`/`section` được **bù theo `article_id`**
> từ `luat-59-2020-qh14-v1` ở bước cuối của `data/doanh-nghiep/chunk_documents.py`
> (hằng `STRUCTURE_FROM`; script đọc `interim/{document_id}.txt` + `registry/documents.json`
> và ghi `processed/chunks.jsonl`). Chỉ metadata cấu trúc được bù, `content` giữ nguyên.
> Hiện trạng đo trên `data/doanh-nghiep/processed/chunks.jsonl`:
>
> | Văn bản | Số chunk | Có `chapter` | Có `section` |
> |---|---|---|---|
> | `luat-59-2020-qh14-v1` | 906 | 906 | 167 |
> | `vbhn-67-vbhn-vpqh-v1` | 916 | 916 (đã bù) | 168 (đã bù) |
> | `nd-168-2025-nd-cp-v1` | 524 | 431 | 0 |
> | 5 văn bản còn lại | 230 | 0 | 0 |
>
> Dù vậy bước Structure Extraction vẫn không được giả định luôn có Chương/Mục: khi
> thiếu và không có văn bản gốc để ánh xạ thì `chapter`/`section` để `null` và ghi
> cảnh báo vào báo cáo xử lý. `scripts/validate_chunks.py` đọc `chunks.jsonl` +
> `registry/documents.json` và kiểm lại `context_header`, `token_count`, tính duy
> nhất của `chunk_id` cùng bảng thống kê trên; chạy sau mỗi lần sinh lại chunk.

### 4.3. Văn bản sửa đổi và văn bản hợp nhất

Văn bản sửa đổi có cấu trúc lồng nhau, ví dụ:

```text
Điều 1. Sửa đổi, bổ sung một số điều của Luật Doanh nghiệp
1. Sửa đổi, bổ sung khoản 2 Điều 17 như sau:
   "2. ..."
```

Nếu chunk trực tiếp, "khoản 2 Điều 17" của Luật Doanh nghiệp sẽ bị gán nhầm
thành "khoản 1 Điều 1" của Luật 76/2025/QH15. Vì vậy:

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

Mỗi văn bản có một bản ghi trong `data/{domain}/registry/documents.json`
(hiện tại: `data/doanh-nghiep/registry/documents.json`). Đây là nguồn dữ liệu cấp
văn bản; metadata cấp chunk được sao chép từ đây
(xem [Metadata Specification](metadata-specification.md)).

```json
{
  "document_key": "luat-59-2020-qh14",
  "document_id": "luat-59-2020-qh14-v1",
  "document_number": "59/2020/QH14",
  "document_type": "luat",
  "document_title": "Luật Doanh nghiệp",
  "issuing_authority": "Quốc hội",
  "issued_date": "2020-06-17",
  "effective_date": "2021-01-01",
  "expiry_date": null,
  "legal_status": "het_hieu_luc_mot_phan",
  "amended_by": ["luat-03-2022-qh15", "luat-76-2025-qh15"],
  "replaces": ["luat-68-2014-qh13"],
  "replaced_by": [],
  "guided_by": ["vbhn-7566-vbhn-bkhdt", "nd-168-2025-nd-cp"],
  "source_url": "https://vbpl.vn/boyte/Pages/vbpq-toanvan.aspx?ItemID=142881",
  "source_format": "html",
  "version": "v1",
  "fetched_at": "2026-10-09T01:40:00Z"
}
```

> **Khoảng cách với registry hiện tại.** Bản ghi thực tế trong
> `data/doanh-nghiep/registry/documents.json` chưa có `document_key`, `version`,
> `expiry_date` và bốn trường quan hệ (`amended_by`, `replaces`, `replaced_by`,
> `guided_by`); bù lại nó có thêm `sha256`, `chars`, `lines`, `article_count`,
> `first_article`, `last_article` và `note` (phạm vi đã cắt của văn bản). Các trường
> quan hệ là phần cần bổ sung để làm được mục 4.3; cho tới lúc đó Team 2 không dựa
> vào chúng.

- `document_key` cố định cho một văn bản, dùng trong các quan hệ
  (`amended_by`, `guided_by`, ...).
- `document_id` = `{document_key}-{version}`, định danh một **phiên bản nội dung**;
  đây là ID xuất hiện trong chunk, citation và URL xem điều luật.

Registry được cập nhật khi có văn bản mới, văn bản bị sửa đổi hoặc thay đổi
trạng thái hiệu lực. Khi nội dung văn bản thay đổi, tăng `version` và sinh
`document_id` mới; không tái sử dụng `document_id` cũ cho nội dung khác để
citation đã lưu vẫn trỏ đúng nội dung.
