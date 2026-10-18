# Retrieval Design

## 1. Mục tiêu

Thiết kế tổng thể luồng tìm kiếm của Team 1: nhận câu hỏi từ Team 2, trả về
danh sách candidate chunk theo `contracts/v0.1/retrieval_output.schema.json`.

Yêu cầu chính:

| Yêu cầu | Giá trị |
|---|---|
| Interface | `retrieve(question, top_k=20)`; `question` 1–4000 code point, `top_k` 1–50 |
| Output | Tối đa `top_k` candidate, `rank` 1..N liên tục, `retrieval_method` ∈ `bm25` \| `dense` \| `hybrid_rrf` |
| Kết quả rỗng | Trả `results: []` khi tìm thành công nhưng không có kết quả |
| Lỗi | Index hỏng / dịch vụ không sẵn sàng / quá thời gian phải **raise lỗi**, không trả `[]` |
| Độ trễ | p95 ≤ 1 giây trên CPU cho `top_k = 20` (ngân sách toàn bộ AI layer là 45 giây theo đặc tả Team 3) |
| Phạm vi văn bản | Chỉ văn bản có `legal_status` ∈ {`con_hieu_luc`, `het_hieu_luc_mot_phan`} |

## 2. Kiến trúc tổng thể

```text
                       OFFLINE — Indexing
┌─────────────────────────────────────────────────────────────────┐
│ data/processed/chunks.jsonl                                     │
│        │                                                        │
│        ├─ lọc legal_status mặc định                             │
│        ├─ search_text = context_header + "\n" + content         │
│        │                                                        │
│        ├──► Vietnamese tokenizer ──► BM25 index (bm25s)         │
│        │                             data/index/bm25/{version}/ │
│        │                                                        │
│        └──► Embedding model ───────► Qdrant collection          │
│                                      legal_chunks_{version}     │
│                                      (vector + payload metadata)│
│                                                                 │
│ Ghi index_manifest.json (version, model, tokenizer, số chunk)   │
└─────────────────────────────────────────────────────────────────┘

                       ONLINE — Query
┌─────────────────────────────────────────────────────────────────┐
│ Team 2: retrieve(question, top_k)                               │
│        │                                                        │
│        ▼                                                        │
│ [1] Validate input + chuẩn hóa query (NFC, khoảng trắng)        │
│        │                                                        │
│        ├──────────────────────┬──────────────────────┐          │
│        ▼                      ▼                      │          │
│ [2a] BM25 search        [2b] Dense search            │ song song│
│      top 100                  top 100 (Qdrant)       │          │
│        │                      │                      │          │
│        └──────────┬───────────┘                      │          │
│                   ▼                                             │
│ [3] Reciprocal Rank Fusion ──► top_k                            │
│                   ▼                                             │
│ [4] Gắn metadata, đặt score / rank / retrieval_method           │
│                   ▼                                             │
│ [5] Trả RetrievalOutput cho Team 2 (rerank)                     │
└─────────────────────────────────────────────────────────────────┘
```

Chi tiết từng nhánh:

- BM25: [BM25 Proposal](bm25-proposal.md)
- Dense: [Dense Retrieval Proposal](dense-retrieval-proposal.md)
- Kết hợp: [Hybrid Retrieval Proposal](hybrid-retrieval-proposal.md)

### 2.1. Vì sao cần cả BM25 và Dense

| Loại câu hỏi | Ví dụ | Phương pháp mạnh hơn |
|---|---|---|
| Có số hiệu, số Điều, thuật ngữ chính xác | "Điều 113 Bộ luật Lao động 45/2019/QH14 quy định gì?" | BM25 — so khớp đúng chuỗi |
| Diễn đạt đời thường, khác từ ngữ trong luật | "Một năm được nghỉ phép bao nhiêu ngày?" | Dense — hiểu "nghỉ phép" ≈ "nghỉ hằng năm" |
| Kết hợp cả hai | "Điều 113 có cho nghỉ gộp phép nhiều năm không?" | Hybrid |

Người dùng hỏi theo cả hai kiểu, nên phương pháp mặc định là `hybrid_rrf`;
`bm25` và `dense` vẫn gọi riêng được để debug và đánh giá.

## 3. Lựa chọn Vector Database

### 3.1. So sánh

Quy mô corpus giai đoạn đầu: vài văn bản, ước tính vài nghìn chunk.

| Tiêu chí | Qdrant | Milvus | Elasticsearch | pgvector (PostgreSQL) |
|---|---|---|---|---|
| Triển khai | 1 container, không phụ thuộc thêm | Standalone vẫn cần etcd + MinIO | JVM, tốn RAM (≥ 2 GB khuyến nghị) | Dùng chung PostgreSQL |
| Dense vector + lọc metadata | Tốt, payload filter và payload index | Tốt | Có (kNN) | Có (HNSW) |
| Sparse vector / BM25 | Sparse vector, IDF tính phía server | Sparse vector, BM25 function (bản mới) | BM25 gốc, mạnh nhất | Cần full-text search riêng |
| Tách từ tiếng Việt | Không tự làm; ta tự tách từ trước | Không tự làm | Cần plugin analyzer tiếng Việt | Không hỗ trợ |
| Hybrid / RRF có sẵn | Có — Query API `prefetch` + `rrf`, có trọng số | Có | Có (RRF retriever) | Không, tự viết |
| Python client | `qdrant-client`, có chế độ local/in-memory để test | `pymilvus` | `elasticsearch` | `psycopg` + SQL |
| Độ phù hợp quy mô hiện tại | Cao | Thấp (quá nặng) | Trung bình | Trung bình |

### 3.2. Quyết định

**Chọn Qdrant** làm vector database.

- Nhẹ nhất để chạy bằng Docker trong `docker-compose.yml` chung của dự án.
- Có payload filter để lọc `legal_status`, `document_type` ngay trong truy vấn vector.
- `qdrant-client` có chế độ chạy local/in-memory, viết unit test không cần server.
- Có sẵn sparse vector và RRF phía server: nếu sau này corpus lớn, chuyển BM25
  vào Qdrant mà không đổi hạ tầng (mục 6).

Không chọn pgvector dù Team 3 đã dùng PostgreSQL: database của Team 3 lưu hội
thoại, gộp chung sẽ ràng buộc vòng đời triển khai hai team, và pgvector không có
hybrid search sẵn.

### 3.3. Vì sao BM25 không đặt trong Qdrant ở MVP

BM25 chạy **trong process** bằng thư viện `bm25s`, không dùng sparse vector của Qdrant:

- Kiểm soát hoàn toàn tách từ tiếng Việt và tham số BM25 (`k1`, `b`), dễ debug
  từng token.
- Corpus vài nghìn chunk, index BM25 chỉ vài MB, nạp vào RAM ngay khi khởi động.
- Sparse BM25 trong Qdrant yêu cầu tự tính phần TF và chuẩn hóa độ dài phía
  client khi dùng tokenizer riêng — phức tạp hơn mà chưa cần ở quy mô này.

Hệ quả: RRF chạy trong code Python của Team 1 (khoảng 20 dòng), không dùng
fusion phía server. Chi tiết ở Hybrid Retrieval Proposal.

## 4. Thành phần và triển khai

### 4.1. Cách Team 2 gọi Team 1

Theo `contracts/v0.1/README.md`, Team 1 và Team 2 chạy chung một Python service
ở MVP. Team 1 cung cấp **thư viện Python**, không phải HTTP service riêng:

```python
from team1_data.retrieval import Retriever

retriever = Retriever.from_config("configs/retrieval.yaml")
output = retriever.retrieve(question="...", top_k=20)          # mặc định hybrid_rrf
output = retriever.retrieve(question="...", top_k=20, method="bm25")
```

`output` là dict hợp lệ theo `retrieval_output.schema.json`.

### 4.2. Lỗi

| Tình huống | Exception | Mã lỗi nội bộ (đặc tả Team 3, mục 1.9) |
|---|---|---|
| Input sai (rỗng, quá dài, `top_k` ngoài 1–50) | `ValueError` | Team 2 trả 400 |
| Qdrant không kết nối được, index BM25 không nạp được | `RetrievalUnavailableError` | `RETRIEVAL_UNAVAILABLE` |
| Quá thời gian (mặc định 5 giây) | `RetrievalTimeoutError` | `RETRIEVAL_TIMEOUT` |
| BM25 và Qdrant lệch phiên bản index | `RetrievalUnavailableError` | `RETRIEVAL_UNAVAILABLE` |

Không fallback âm thầm: nếu một nhánh (BM25 hoặc Dense) lỗi khi đang ở chế độ
`hybrid_rrf` thì raise lỗi, không trả kết quả của nhánh còn lại dưới nhãn
`hybrid_rrf`. Có thể cấu hình fallback tường minh sau, khi đó `retrieval_method`
phải ghi đúng phương pháp đã chạy.

### 4.3. Phiên bản index

- Mỗi lần build index sinh `index_version` (ví dụ `2026-10-04-01`).
- BM25 lưu tại `data/index/bm25/{index_version}/`; Qdrant collection tên
  `legal_chunks_{index_version}`, truy cập qua alias `legal_chunks`.
- `index_manifest.json` ghi: `index_version`, `pipeline_version`, tên và revision
  mô hình embedding, tokenizer, số chunk, danh sách `chunk_id` (hoặc hash của nó).
- Khi khởi động, `Retriever` kiểm tra hai index có cùng `index_version` và cùng
  tập `chunk_id`; lệch thì từ chối chạy.
- Build index mới xong mới chuyển alias (blue-green), không sửa index đang phục vụ.

### 4.4. Cấu hình

`configs/retrieval.yaml` (không chứa secret):

```yaml
index_version: "2026-10-04-01"
default_method: hybrid_rrf
timeout_seconds: 5
bm25:
  index_dir: data/index/bm25
  candidates: 100
dense:
  qdrant_url: http://localhost:6333
  collection_alias: legal_chunks
  model: AITeamVN/Vietnamese_Embedding
  candidates: 100
hybrid:
  rrf_k: 60
  weights: { bm25: 1.0, dense: 1.0 }
filters:
  legal_status: [con_hieu_luc, het_hieu_luc_mot_phan]
```

### 4.5. Dịch vụ cần thêm vào `docker-compose.yml`

```yaml
qdrant:
  image: qdrant/qdrant:<phiên bản cố định>
  ports: ["6333:6333"]
  volumes: ["./data/qdrant:/qdrant/storage"]
```

Phiên bản image phải cố định (không dùng `latest`) và thống nhất với Team 3,
team sở hữu deployment.

## 5. Đánh giá retrieval

| Hạng mục | Nội dung |
|---|---|
| Bộ dữ liệu | 100–200 câu hỏi, mỗi câu gán nhãn `article_id` (và `chunk_id` nếu xác định được) đúng; gồm cả câu hỏi có số hiệu và câu hỏi diễn đạt đời thường |
| Chỉ số | Recall@5, Recall@20 (Team 2 nhận 20 candidate), MRR@10, nDCG@10 |
| So sánh | `bm25`, `dense`, `hybrid_rrf` trên cùng bộ câu hỏi và cùng index |
| Độ trễ | p50 / p95 của `retrieve()` |
| Ngưỡng chấp nhận ban đầu | Recall@20 của `hybrid_rrf` ≥ 0.90 và không thấp hơn nhánh tốt nhất |

Recall@20 quan trọng nhất: chunk đúng không có trong 20 candidate thì reranker
của Team 2 không thể cứu được.

## 6. Hướng mở rộng

| Khi nào | Thay đổi |
|---|---|
| Corpus > ~100.000 chunk hoặc nhiều process cùng phục vụ | Chuyển BM25 thành sparse vector trong Qdrant, dùng `prefetch` + `rrf` phía server |
| Câu hỏi thường chứa số hiệu / số Điều | Thêm bước trích xuất tham chiếu pháp lý từ query để lọc hoặc ưu tiên đúng văn bản/Điều |
| Có văn bản hết hiệu lực trong corpus | Cho phép Team 2 truyền bộ lọc hiệu lực theo ngày (cần cập nhật contract) |
