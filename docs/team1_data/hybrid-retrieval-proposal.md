# Hybrid Retrieval Proposal

## 1. Mục tiêu

Đề xuất cách kết hợp kết quả của [BM25](bm25-proposal.md) và
[Dense Retrieval](dense-retrieval-proposal.md) thành một danh sách duy nhất,
trả cho Team 2 với `retrieval_method = "hybrid_rrf"`.

## 2. Vấn đề: điểm của hai nhánh không cùng thang đo

| Nhánh | Thang điểm | Ví dụ điểm top 3 của một câu hỏi |
|---|---|---|
| BM25 | 0 → không giới hạn, thay đổi theo từng câu hỏi | 18.2, 9.1, 8.7 |
| Dense (cosine) | −1 → 1, thực tế thường dồn trong khoảng hẹp | 0.83, 0.81, 0.80 |

Cộng thẳng hai điểm thì BM25 luôn áp đảo. Muốn cộng có trọng số thì phải chuẩn
hóa trước, và việc chuẩn hóa lại có nhược điểm riêng (mục 3).

## 3. So sánh phương pháp

| Tiêu chí | **RRF** (Reciprocal Rank Fusion) | Weighted Score (chuẩn hóa + trọng số α) | DBSF (Distribution-Based Score Fusion) |
|---|---|---|---|
| Dùng gì | Chỉ **thứ hạng** | Giá trị điểm | Giá trị điểm, chuẩn hóa theo phân phối |
| Cần chuẩn hóa điểm | Không | Có (min-max hoặc z-score) | Có (tự làm theo mean ± 3σ) |
| Nhạy với điểm ngoại lai | Không | Có: một điểm BM25 rất cao làm các điểm khác bị nén về gần 0 | Ít hơn |
| Khi một nhánh không có kết quả | Tự nhiên: nhánh đó đóng góp 0 | Min-max không xác định (chia cho 0), cần xử lý riêng | Cần xử lý riêng |
| Tham số cần tinh chỉnh | `k` (ít nhạy), trọng số tùy chọn | `α` (nhạy, phụ thuộc model và dữ liệu) | Ít |
| Phổ biến | Có sẵn trong Qdrant, Elasticsearch, OpenSearch, Milvus | Phổ biến nhưng cần tinh chỉnh nhiều | Có trong Qdrant |
| Contract v0.1 | **Đã có**: `hybrid_rrf` | Chưa có giá trị enum | Chưa có giá trị enum |

**Chọn RRF**, có hỗ trợ trọng số cho từng nhánh.

- Không cần chuẩn hóa điểm, không bị ảnh hưởng khi BM25 và cosine thay đổi thang
  đo theo từng câu hỏi hoặc khi đổi model embedding.
- Hoạt động ổn định ngay với tham số mặc định, chưa cần dữ liệu để tinh chỉnh.
- Đúng giá trị `retrieval_method` đã chốt trong contract với Team 2.

Weighted Score được giữ làm thử nghiệm (mục 7). Nếu nó vượt RRF rõ rệt, cần
bổ sung giá trị enum mới (ví dụ `hybrid_weighted`) trong contract v0.2 trước khi dùng.

## 4. Công thức RRF

```text
RRF(d) = Σ  w_i / (k + rank_i(d))
         i
```

- `rank_i(d)`: thứ hạng của chunk `d` trong danh sách của nhánh `i`, **bắt đầu từ 1**.
- Chunk không có trong danh sách của nhánh `i` thì nhánh đó đóng góp **0**.
- `k`: hằng số làm mượt; `k` lớn thì chênh lệch giữa hạng 1 và hạng 10 nhỏ lại.
- `w_i`: trọng số nhánh, mặc định 1.0.

Ý nghĩa trực quan: chunk được **cả hai nhánh** xếp cao sẽ đứng đầu; chunk chỉ
một nhánh tìm thấy vẫn được giữ, nhưng xếp sau.

### 4.1. Ví dụ tính tay

`k = 60`, trọng số 1.0 / 1.0. BM25 trả `[A, C, B, E]`, Dense trả `[B, D, E, F, A]`:

| Chunk | Hạng BM25 | Hạng Dense | Tính | RRF | Hạng cuối |
|---|---:|---:|---|---:|---:|
| B | 3 | 1 | 1/63 + 1/61 | 0.0323 | **1** |
| A | 1 | 5 | 1/61 + 1/65 | 0.0318 | 2 |
| E | 4 | 3 | 1/64 + 1/63 | 0.0315 | 3 |
| C | 2 | — | 1/62 | 0.0161 | 4 |
| D | — | 2 | 1/62 | 0.0161 | 5 |
| F | — | 4 | 1/64 | 0.0156 | 6 |

Nhận xét:

- A đứng đầu BM25 nhưng B lên hạng 1 vì **cả hai nhánh** đều xếp B cao.
- C đứng thứ 2 ở BM25 nhưng tụt xuống thứ 4 vì Dense không tìm thấy.
- C và D bằng điểm; phân xử theo quy tắc ở mục 5.3.

## 5. Thiết kế chi tiết

### 5.1. Tham số

| Tham số | Giá trị khởi đầu | Ghi chú |
|---|---:|---|
| `rrf_k` | 60 | Giá trị trong bài báo gốc (Cormack, Clarke & Büttcher, 2009), dùng phổ biến làm mặc định |
| `weights` | BM25 1.0, Dense 1.0 | Tinh chỉnh sau khi có bộ đánh giá |
| Số candidate mỗi nhánh | 100 | Lớn hơn nhiều so với `top_k = 20` để chunk chỉ đứng hạng 30–50 ở một nhánh nhưng cao ở nhánh kia vẫn được xét |
| `top_k` đầu ra | Team 2 truyền vào (mặc định 20, tối đa 50) | Theo contract |

### 5.2. Luồng xử lý

```text
question
  ├─► BM25  → 100 chunk_id theo hạng   ┐
  └─► Dense → 100 chunk_id theo hạng   ┤  chạy song song
                                       ▼
                     RRF fuse (gộp theo chunk_id)
                                       ▼
                     sắp xếp + phân xử bằng điểm, cắt top_k
                                       ▼
                     gắn metadata, score = RRF, rank = 1..N,
                     retrieval_method = "hybrid_rrf"
```

### 5.3. Phân xử bằng điểm (tie-break)

Khi hai chunk cùng điểm RRF, xếp theo thứ tự ưu tiên:

1. Hạng tốt nhất của chunk ở bất kỳ nhánh nào (nhỏ hơn đứng trước).
2. `chunk_id` theo thứ tự từ điển.

Quy tắc này làm kết quả **xác định**: cùng câu hỏi, cùng index luôn ra cùng thứ
tự — cần thiết để test và để đánh giá lặp lại được.

### 5.4. Điểm số trong output

- `score` = điểm RRF. Với hai nhánh trọng số 1.0 và `k = 60`, điểm tối đa là
  2/61 ≈ 0.0328.
- Điểm RRF chỉ có ý nghĩa **so sánh thứ hạng trong cùng một câu hỏi**. Không phải
  xác suất, không dùng làm ngưỡng "đủ căn cứ" — phù hợp ghi chú của contract
  ("điểm kỹ thuật, không phải xác suất đúng").

### 5.5. Kết quả rỗng và lỗi

| Tình huống | Kết quả |
|---|---|
| Cả hai nhánh chạy thành công, đều không có kết quả | `results: []` |
| BM25 không có token nào khớp (trả rỗng), Dense có kết quả | Trả kết quả theo RRF (thực chất là thứ tự của Dense), vẫn ghi `hybrid_rrf` — đây là kết quả hợp lệ, không phải lỗi |
| Một nhánh **lỗi** (Qdrant không kết nối được, index BM25 không nạp được) | Raise `RetrievalUnavailableError`; không trả kết quả của nhánh còn lại dưới nhãn `hybrid_rrf` (Retrieval Design mục 4.2) |

### 5.6. Phác thảo code

```python
def rrf_fuse(
    ranked_lists: list[list[str]],
    k: int = 60,
    weights: list[float] | None = None,
    top_k: int = 20,
) -> list[tuple[str, float]]:
    weights = weights or [1.0] * len(ranked_lists)
    scores: dict[str, float] = {}
    best_rank: dict[str, int] = {}
    for ids, w in zip(ranked_lists, weights):
        for rank, chunk_id in enumerate(ids, start=1):
            scores[chunk_id] = scores.get(chunk_id, 0.0) + w / (k + rank)
            best_rank[chunk_id] = min(best_rank.get(chunk_id, rank), rank)
    ordered = sorted(scores, key=lambda c: (-scores[c], best_rank[c], c))
    return [(c, scores[c]) for c in ordered[:top_k]]
```

Đoạn code này đã được chạy thử với ví dụ ở mục 4.1 và cho đúng bảng kết quả;
với hai danh sách rỗng trả `[]`.

## 6. Hướng chuyển sang RRF phía server

Khi BM25 được chuyển thành sparse vector trong Qdrant (Retrieval Design mục 6),
có thể thay `rrf_fuse` bằng Query API của Qdrant: hai `prefetch` (`dense` và
`bm25`) cộng truy vấn `rrf` có trọng số. Trước khi chuyển, chạy cả hai cách trên
bộ đánh giá để xác nhận kết quả tương đương (cần kiểm tra giá trị `k` và quy
tắc tie-break phía server).

## 7. Thử nghiệm

Trên bộ đánh giá chung (Retrieval Design mục 5):

| Thử nghiệm | Giá trị |
|---|---|
| So sánh phương pháp | `bm25`, `dense`, `hybrid_rrf` |
| `rrf_k` | 10, 30, 60, 100 |
| Trọng số BM25 : Dense | 1:1, 1:2, 2:1 |
| Số candidate mỗi nhánh | 50, 100, 200 |
| Đối chứng Weighted Score | Min-max mỗi nhánh, `α` (trọng số Dense) ∈ {0.3, 0.5, 0.7} |

Tiêu chí chấp nhận: Recall@20 của `hybrid_rrf` không thấp hơn nhánh đơn tốt
nhất, và cao hơn trên nhóm câu hỏi có cả số hiệu lẫn diễn đạt đời thường.
