# Chunk Format Specification

## 1. Mục tiêu

Định nghĩa cách chia văn bản pháp luật thành các chunk phục vụ BM25 và Dense
Retrieval, sao cho:

- Mỗi chunk **tự đủ nghĩa** khi đứng một mình (Team 2 đưa thẳng vào prompt).
- Mỗi chunk **trích dẫn được** tới đúng Điều/Khoản/Điểm.
- Kích thước nằm trong giới hạn của mô hình embedding và ngân sách context
  của Team 2 (tối đa 5 chunk sau rerank).

## 2. Chiến lược: chunk theo cấu trúc, không cắt theo số ký tự cố định

Cắt cố định (ví dụ mỗi 500 ký tự) sẽ cắt ngang Khoản, trộn hai Khoản khác nhau
vào một chunk và làm sai citation. Văn bản pháp luật đã có sẵn đơn vị ngữ nghĩa
là Khoản, nên dùng Khoản làm đơn vị chunk mặc định và chỉ cắt nhỏ hơn khi bắt buộc.

### 2.1. Quy tắc chia

| Quy tắc | Điều kiện | Cách chia | `clause` | `point` |
|---|---|---|---|---|
| R1 | Điều **không có** Khoản, độ dài ≤ `MAX_TOKENS` | Cả Điều là 1 chunk | `null` | `null` |
| R2 | Điều có Khoản; Khoản ≤ `MAX_TOKENS` | **Mỗi Khoản là 1 chunk** (quy tắc mặc định) | `Khoản n` | `null` |
| R3 | Khoản > `MAX_TOKENS` và có các Điểm | Gom các Điểm liên tiếp thành nhóm ≤ `MAX_TOKENS`; **mỗi nhóm lặp lại câu dẫn của Khoản** | `Khoản n` | `null` nếu nhóm nhiều Điểm; `Điểm x` nếu nhóm chỉ có 1 Điểm |
| R4 | Một đoạn vẫn > `MAX_TOKENS` sau R1–R3 (Điều không Khoản dài, Khoản không Điểm dài, hoặc một Điểm dài) | Cắt theo ranh giới câu (`.` `;`) thành cửa sổ `TARGET_TOKENS`, **overlap `OVERLAP_TOKENS`** | giữ theo đơn vị cha | giữ theo đơn vị cha |

Thứ tự áp dụng: R1/R2 trước, chỉ khi quá dài mới xuống R3, rồi R4.

### 2.2. Câu dẫn — vì sao bắt buộc lặp lại

Ví dụ có thật — Điều 137 khoản 1 Bộ luật Lao động 2019:

```text
1. Người sử dụng lao động không được sử dụng người lao động làm việc ban đêm,
làm thêm giờ và đi công tác xa trong trường hợp sau đây:
a) Mang thai từ tháng thứ 07 hoặc từ tháng thứ 06 nếu làm việc ở vùng cao, vùng sâu,
vùng xa, biên giới, hải đảo;
b) Đang nuôi con dưới 12 tháng tuổi, trừ trường hợp được người lao động đồng ý.
```

Nếu tách Điểm a) ra thành chunk riêng mà **không có câu dẫn**, chunk chỉ còn
"Mang thai từ tháng thứ 07 hoặc từ tháng thứ 06 nếu làm việc ở vùng cao..." —
mất hoàn toàn vế "người sử dụng lao động không được sử dụng", chunk trở nên vô
nghĩa và LLM có thể hiểu ngược. Vì vậy:

- Câu dẫn của **Khoản** (phần trước Điểm a) được lặp lại ở đầu mọi chunk R3.
- Câu dẫn của **Điều** (`article_intro`, phần trước Khoản 1 nếu có) được đưa
  vào `context_header` của mọi chunk thuộc Điều đó.

### 2.3. Overlap

| Trường hợp | Overlap | Lý do |
|---|---|---|
| R1, R2, R3 (cắt theo ranh giới cấu trúc) | **0** | Mỗi Khoản/nhóm Điểm là đơn vị pháp lý độc lập; ngữ cảnh đã được bù bằng `context_header` và câu dẫn. Overlap ở đây chỉ làm hai chunk chứa nội dung của Khoản khác, gây trích dẫn sai |
| R4 (cắt theo câu trong một đoạn dài) | **64 token** (~15% của `TARGET_TOKENS`) | Câu ở ranh giới cắt có thể phụ thuộc câu trước; overlap giữ liền mạch ý. Overlap luôn là **câu trọn vẹn**, không cắt giữa câu |

Có thể hiểu `context_header` + câu dẫn là một dạng "overlap ngữ nghĩa": thay vì
lặp lại vài câu của chunk bên cạnh, mỗi chunk mang theo đúng phần ngữ cảnh cha
mà nó cần.

## 3. Tham số

Đơn vị token tính bằng **tokenizer của mô hình embedding chính**
(xem [Dense Retrieval Proposal](dense-retrieval-proposal.md)), không tính bằng
số từ hay số ký tự.

| Tham số | Giá trị khởi đầu | Áp dụng cho | Ghi chú |
|---|---:|---|---|
| `MAX_TOKENS` | 512 | `context_header` + `content` | Giới hạn trên của mọi chunk |
| `TARGET_TOKENS` | 384 | Cửa sổ R4 | Chừa chỗ cho header và overlap |
| `OVERLAP_TOKENS` | 64 | Chỉ R4 | Làm tròn tới ranh giới câu |
| `MIN_TOKENS` | 20 | Cảnh báo | Chunk quá ngắn được giữ nguyên (không gộp với Khoản khác để không sai citation) nhưng ghi vào báo cáo |

Lý do chọn 512 dù mô hình chính hỗ trợ tới 2048 token:

- Chunk nhỏ cho embedding "tập trung" hơn, truy hồi chính xác tới Khoản.
- Team 2 chọn tối đa 5 chunk: 5 × 512 ≈ 2.560 token context, vừa ngân sách prompt.
- Nếu dùng mô hình baseline giới hạn 256 token (BKAI bi-encoder) để so sánh,
  phần vượt 256 sẽ bị cắt khi embed; ghi nhận điều này trong kết quả benchmark.

Các giá trị này là **mặc định để triển khai**, được điều chỉnh sau khi đo ở
giai đoạn Retrieval Evaluation (mục 6).

## 4. Cấu trúc một chunk

| Trường | Ý nghĩa |
|---|---|
| `content` | Nguyên văn đoạn luật của chunk (đã qua cleaning), gồm câu dẫn Khoản nếu là R3. Đây là text Team 2 đưa vào prompt và trích dẫn |
| `context_header` | Đường dẫn cấu trúc + câu dẫn Điều, **không** phải nguyên văn của chunk. Dùng để ghép vào text tìm kiếm và để Team 2 hiển thị ngữ cảnh |
| `chunk_index` / `chunk_count` | Thứ tự chunk con khi một Khoản/Điều bị chia (R3, R4); bằng 0 / 1 nếu không chia |

Định dạng `context_header`:

```text
{document_title} {document_number} > {chapter} {chapter_title} > {section} > {article} {article_title}
[câu dẫn Điều, nếu có]
```

Ví dụ:

```text
Bộ luật Lao động 45/2019/QH14 > Chương VII. Thời giờ làm việc, thời giờ nghỉ ngơi > Mục 2. Thời giờ nghỉ ngơi > Điều 113. Nghỉ hằng năm
```

Text dùng để index (không lưu thành trường riêng, sinh ở bước indexing):

```text
search_text = context_header + "\n" + content
```

Toàn bộ trường metadata khác: xem [Metadata Specification](metadata-specification.md).

## 5. Đơn vị Điều đầy đủ (article store)

Ngoài chunk, pipeline xuất thêm `data/processed/articles.jsonl`, mỗi dòng là
**toàn văn một Điều** khóa theo (`document_id`, `article_id`). Dùng cho:

- API xem nguyên văn điều luật của Team 3
  (`GET /internal/v1/documents/{document_id}/articles/{article_id}`).
- Team 2 mở rộng context từ chunk lên cả Điều khi cần (small-to-big), nếu
  thiết kế context builder chọn hướng này.

Article store không được index để tìm kiếm, tránh trùng kết quả với chunk.

## 6. Kế hoạch thử nghiệm

So sánh trên cùng bộ câu hỏi đánh giá, đo Recall@5, Recall@20 và MRR@10:

| Cấu hình | Mô tả |
|---|---|
| A (mặc định) | Theo Khoản, R1–R4, `MAX_TOKENS` = 512 |
| B | Theo Điều (mỗi Điều 1 chunk, Điều dài cắt R4) |
| C | Theo Khoản, `MAX_TOKENS` = 256 |
| D (đối chứng) | Cắt cố định 512 token, overlap 64, bỏ qua cấu trúc |

Có kết quả thì cập nhật bảng tham số mục 3 và ghi lý do thay đổi.
