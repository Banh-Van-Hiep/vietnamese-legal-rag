# Metadata Specification

## 1. Mục tiêu

Xác định các trường thông tin đi kèm mỗi chunk, quy tắc sinh ID và cách ánh xạ
sang contract retrieval gửi Team 2. Schema máy đọc:
[`schemas/chunk_metadata.schema.json`](schemas/chunk_metadata.schema.json).

Metadata phục vụ bốn việc:

1. **Trích dẫn**: Team 2 tạo citation từ metadata thật, không để LLM tự sinh.
2. **Xem nguyên văn**: Team 3 mở điều luật bằng `document_id` + `article_id`.
3. **Lọc khi tìm kiếm**: loại văn bản hết hiệu lực, lọc theo loại văn bản.
4. **Truy vết**: biết chunk đến từ phiên bản văn bản nào, pipeline nào.

## 2. Danh sách trường

Ký hiệu cột **Contract**: ✔ = trường được gửi sang Team 2 trong Retrieval Output
(`contracts/v0.1/retrieval_output.schema.json`); để trống = chỉ lưu trong index
để lọc/truy vết.

### 2.1. Định danh

| Trường | Kiểu | Bắt buộc | Contract | Ví dụ | Mô tả |
|---|---|---|---|---|---|
| `chunk_id` | string ≤ 200 | ✔ | ✔ | `bl-45-2019-qh14-v1__dieu-113__k1__0` | ID duy nhất của chunk |
| `document_id` | string ≤ 200, `^[A-Za-z0-9_-]+$` | ✔ | ✔ | `bl-45-2019-qh14-v1` | ID **phiên bản** văn bản; không tái sử dụng khi nội dung đổi |
| `document_key` | string, `^[a-z0-9-]+$` | ✔ | | `bl-45-2019-qh14` | ID cố định của văn bản qua các phiên bản |
| `article_id` | string ≤ 100, `^[A-Za-z0-9_-]+$` | ✔ | ✔ | `dieu-113` | ID Điều trong văn bản, dùng trong URL xem điều luật |
| `version` | string | ✔ | | `v1` | Phiên bản nội dung văn bản |

### 2.2. Thông tin văn bản (sao chép từ registry)

| Trường | Kiểu | Bắt buộc | Contract | Ví dụ | Mô tả |
|---|---|---|---|---|---|
| `document_title` | string ≤ 500 | ✔ | ✔ | `Bộ luật Lao động` | Tên văn bản |
| `document_number` | string | ✔ | | `45/2019/QH14` | **Số hiệu VBPL** đúng như trên văn bản |
| `document_type` | enum | ✔ | | `luat` | **Loại văn bản** (mục 3.1) |
| `issuing_authority` | string | ✔ | | `Quốc hội` | Cơ quan ban hành |
| `issued_date` | date `YYYY-MM-DD` | ✔ | | `2020-06-17` | **Ngày ban hành** |
| `effective_date` | date | ✔ | | `2021-01-01` | Ngày có hiệu lực |
| `expiry_date` | date \| null | ✔ | | `null` | Ngày hết hiệu lực; `null` nếu còn hiệu lực |
| `legal_status` | enum | ✔ | | `con_hieu_luc` | Trạng thái hiệu lực (mục 3.2) |
| `source_url` | string HTTPS ≤ 2048 | ✔ | ✔ | `https://vbpl.vn/...` | Nguồn chính thức |

### 2.3. Vị trí trong cấu trúc (Điều/Khoản gốc)

| Trường | Kiểu | Bắt buộc | Contract | Ví dụ | Mô tả |
|---|---|---|---|---|---|
| `part` | string \| null | ✔ (có key) | | `null` | Phần |
| `chapter` | string \| null | ✔ (có key) | | `Chương II` | Chương |
| `chapter_title` | string \| null | ✔ (có key) | | `Thời giờ làm việc, thời giờ nghỉ ngơi` | Tên chương |
| `section` | string \| null | ✔ (có key) | | `null` | Mục |
| `section_title` | string \| null | ✔ (có key) | | `null` | Tên mục |
| `article` | string ≤ 100 | ✔ | ✔ | `Điều 113` | Nhãn hiển thị Điều |
| `article_title` | string | ✔ | | `Quyền thành lập, góp vốn, ...` | Tên Điều |
| `clause` | string ≤ 100 \| null | ✔ (có key) | ✔ | `Khoản 2` | `null` nếu chunk là cả Điều (R1) |
| `point` | string ≤ 100 \| null | ✔ (có key) | ✔ | `null` | `Điểm a` khi chunk chỉ chứa đúng một Điểm |

Nhãn hiển thị luôn có tiền tố: `Điều 113`, `Khoản 1`, `Điểm đ` — không lưu số trần.

### 2.4. Nội dung

| Trường | Kiểu | Bắt buộc | Contract | Mô tả |
|---|---|---|---|---|
| `content` | string 1–20000 | ✔ | ✔ | Nguyên văn đoạn luật của chunk |
| `context_header` | string | ✔ | | Đường dẫn cấu trúc + câu dẫn Điều (xem Chunk Format mục 4) |
| `chunk_index` | integer ≥ 0 | ✔ | | Thứ tự chunk con trong cùng Khoản/Điều |
| `chunk_count` | integer ≥ 1 | ✔ | | Tổng số chunk con của Khoản/Điều đó |
| `token_count` | integer | ✔ | | Số token của `context_header` + `content` |

### 2.5. Sửa đổi và truy vết

| Trường | Kiểu | Bắt buộc | Mô tả |
|---|---|---|---|
| `amended_by` | array\<string\> | ✔ | `document_key` của các văn bản đã sửa đổi Điều này; `[]` nếu không có |
| `amendment_notes` | array\<string\> | ✔ | Chú thích sửa đổi lấy từ VBHN (Data Processing Flow, C8); `[]` nếu không có |
| `pipeline_version` | string | ✔ | Phiên bản quy tắc cleaning/chunking đã sinh ra chunk |

## 3. Giá trị enum

### 3.1. `document_type`

| Giá trị | Hiển thị | Tiền tố trong `document_key` |
|---|---|---|
| `hien_phap` | Hiến pháp | `hp` |
| `bo_luat` | Bộ luật | `bl` |
| `luat` | Luật | `luat` |
| `nghi_quyet` | Nghị quyết | `nq` |
| `nghi_dinh` | Nghị định | `nd` |
| `quyet_dinh` | Quyết định | `qd` |
| `thong_tu` | Thông tư | `tt` |
| `van_ban_hop_nhat` | Văn bản hợp nhất | `vbhn` |

### 3.2. `legal_status`

| Giá trị | Ý nghĩa | Index mặc định |
|---|---|---|
| `con_hieu_luc` | Còn hiệu lực | Có |
| `het_hieu_luc_mot_phan` | Hết hiệu lực một phần | Có |
| `chua_co_hieu_luc` | Đã ban hành, chưa đến ngày hiệu lực | Không (bật khi cần) |
| `het_hieu_luc` | Hết hiệu lực toàn bộ | Không |

Bộ lọc mặc định khi truy hồi: `legal_status ∈ {con_hieu_luc, het_hieu_luc_mot_phan}`.

## 4. Quy tắc sinh ID

Mọi ID sinh **xác định** (deterministic) từ dữ liệu, chạy lại cho cùng kết quả.

### 4.1. `document_key`

```text
{tiền tố loại}-{số hiệu đã chuẩn hóa}
```

Chuẩn hóa số hiệu: bỏ dấu tiếng Việt (`Đ` → `d`), chữ thường, `/` và khoảng
trắng → `-`, gộp nhiều `-` liền nhau.

| Loại | Số hiệu | `document_key` |
|---|---|---|
| Bộ luật | 45/2019/QH14 | `bl-45-2019-qh14` |
| Luật | 71/2025/QH15 | `luat-71-2025-qh15` |
| Nghị định | 145/2020/NĐ-CP | `nd-145-2020-nd-cp` |
| Nghị định | 293/2025/NĐ-CP | `nd-293-2025-nd-cp` |
| Thông tư | 10/2020/TT-BLĐTBXH | `tt-10-2020-tt-bldtbxh` |
| Văn bản hợp nhất | 125/VBHN-VPQH | `vbhn-125-vbhn-vpqh` |

### 4.2. `document_id`

```text
{document_key}-{version}        ví dụ: bl-45-2019-qh14-v1
```

Tăng `version` khi nội dung văn bản trong corpus thay đổi (cập nhật VBHN, sửa
lỗi trích xuất làm đổi text). Phiên bản cũ vẫn giữ trong article store để
citation đã lưu ở Team 3 tiếp tục mở được.

### 4.3. `article_id`

```text
dieu-{số Điều, chữ thường}      ví dụ: dieu-113, dieu-113a
pl-{số phụ lục}                 ví dụ: pl-1 (khi xử lý phụ lục)
```

### 4.4. `chunk_id`

```text
{document_id}__{article_id}__k{số Khoản hoặc 0}__{chunk_index}
```

- `k0` khi chunk không thuộc Khoản nào (R1, Điều không có Khoản).
- `chunk_index` bắt đầu từ 0.
- Dùng `__` (hai gạch dưới) làm ranh giới để tách ngược được các thành phần.

Ví dụ: `bl-45-2019-qh14-v1__dieu-113__k1__0`, `nd-145-2020-nd-cp-v1__dieu-65__k0__1`.

## 5. Ánh xạ sang Retrieval Output (Team 1 → Team 2)

Contract `retrieval_output.schema.json` dùng `additionalProperties: false`, nên
Team 1 **chỉ gửi đúng các trường có dấu ✔** ở mục 2, cộng ba trường sinh lúc truy hồi:

| Trường contract | Nguồn |
|---|---|
| `chunk_id`, `document_id`, `article_id`, `content`, `document_title`, `article`, `clause`, `point`, `source_url` | Sao chép nguyên từ chunk metadata |
| `score` | Điểm của phương pháp truy hồi (BM25, cosine hoặc RRF) |
| `rank` | Thứ tự 1..N liên tục sau khi xếp hạng |
| `retrieval_method` | `bm25` \| `dense` \| `hybrid_rrf` |

Ánh xạ từ tên trường cũ (bản đặc tả trước và schema cũ của Team 2):

| Tên cũ | Tên mới |
|---|---|
| `document` | `document_title` |
| `source` | `source_url` |
| `chapter` | `chapter` (giữ, không gửi trong contract) |

### 5.1. Đề xuất bổ sung contract v0.2

Citation pháp luật thường cần số hiệu và ngày ban hành (ví dụ "khoản 1 Điều 113
Bộ luật Lao động số 45/2019/QH14"). Contract v0.1 chưa có các trường này. Đề
xuất Team 2 và Team 3 xem xét bổ sung vào v0.2:

- `document_number`
- `issued_date`
- `legal_status`

Cho tới khi contract được cập nhật, Team 1 không gửi các trường này để giữ
tương thích với `additionalProperties: false`.

## 6. Ví dụ chunk đầy đủ

```json
{
  "chunk_id": "bl-45-2019-qh14-v1__dieu-113__k1__0",
  "document_id": "bl-45-2019-qh14-v1",
  "document_key": "bl-45-2019-qh14",
  "article_id": "dieu-113",
  "version": "v1",

  "document_title": "Bộ luật Lao động",
  "document_number": "45/2019/QH14",
  "document_type": "bo_luat",
  "issuing_authority": "Quốc hội",
  "issued_date": "2019-11-20",
  "effective_date": "2021-01-01",
  "expiry_date": null,
  "legal_status": "con_hieu_luc",
  "source_url": "https://vbpl.vn/...",

  "part": null,
  "chapter": "Chương VII",
  "chapter_title": "Thời giờ làm việc, thời giờ nghỉ ngơi",
  "section": "Mục 2",
  "section_title": "Thời giờ nghỉ ngơi",
  "article": "Điều 113",
  "article_title": "Nghỉ hằng năm",
  "clause": "Khoản 1",
  "point": null,

  "content": "1. Người lao động làm việc đủ 12 tháng cho một người sử dụng lao động thì được nghỉ hằng năm, hưởng nguyên lương theo hợp đồng lao động như sau:\na) 12 ngày làm việc đối với người làm công việc trong điều kiện bình thường;\nb) 14 ngày làm việc đối với người lao động chưa thành niên, lao động là người khuyết tật, người làm nghề, công việc nặng nhọc, độc hại, nguy hiểm;\nc) 16 ngày làm việc đối với người làm nghề, công việc đặc biệt nặng nhọc, độc hại, nguy hiểm.",
  "context_header": "Bộ luật Lao động 45/2019/QH14 > Chương VII. Thời giờ làm việc, thời giờ nghỉ ngơi > Mục 2. Thời giờ nghỉ ngơi > Điều 113. Nghỉ hằng năm",
  "chunk_index": 0,
  "chunk_count": 1,
  "token_count": 198,

  "amended_by": [],
  "amendment_notes": [],
  "pipeline_version": "1.0.0"
}
```

Giá trị `amended_by` và `token_count` trong ví dụ chỉ minh họa cấu trúc.
