# Dense Retrieval Proposal

## 1. Mục tiêu

Chọn mô hình embedding tiếng Việt và chiến lược indexing vector cho nhánh tìm
kiếm ngữ nghĩa (semantic) trong [Retrieval Design](retrieval-design.md).

Dense retrieval biến câu hỏi và chunk thành vector; hai đoạn **cùng nghĩa** thì
vector gần nhau, kể cả khi không trùng từ. Ví dụ "nghỉ phép năm" và "nghỉ hằng
năm", hay "bị đuổi việc" và "đơn phương chấm dứt hợp đồng lao động" — BM25
không khớp được, dense retrieval thì có.

## 2. Lựa chọn mô hình embedding

### 2.1. Ứng viên

| Mô hình | Kiến trúc / gốc | Tham số | Chiều vector | Max token | Cần tách từ? | Giấy phép | Ghi chú |
|---|---|---|---:|---:|---|---|---|
| `AITeamVN/Vietnamese_Embedding` | Encoder, fine-tune từ BGE-M3 | ~568M | 1024 | 2048 | Không | Apache-2.0 | Fine-tune cho retrieval tiếng Việt; tác giả báo cáo MRR@10 = 0.818 trên tập Zalo Legal 2021 và cho biết **không** huấn luyện trên tập này |
| `darklethelong/vnlegal-lal` | Decoder (Qwen3), fine-tune từ `vietlegal-harrier-0.6b` | ~600M | 1024 | 2048 | Không | Apache-2.0 | Chuyên luật; tự báo cáo NDCG@10 = 0.849 trên MTEB ZacLegalTextRetrieval |
| `mainguyen9/vietlegal-harrier-0.6b` | Decoder (Qwen3), fine-tune từ `microsoft/harrier-oss-v1-0.6b` | ~600M | 1024 | 512 | Không | Apache-2.0 | Chuyên luật; tự báo cáo NDCG@10 = 0.781 |
| `mainguyen9/vietlegal-e5` | Encoder, fine-tune từ `multilingual-e5-large` | ~560M | 1024 (Matryoshka 128–1024) | 512 | Không | Apache-2.0 | Cần tiền tố `query: ` / `passage: ` |
| `bkai-foundation-models/vietnamese-bi-encoder` | Encoder PhoBERT | ~135M | 768 | 256 | **Có** (PyVi) | Apache-2.0 | Nhỏ, nhanh; đã dùng một phần tập train Zalo Legal để huấn luyện |
| `BAAI/bge-m3` | Encoder đa ngôn ngữ | ~568M | 1024 | 8192 | Không | MIT | Mốc so sánh đa ngôn ngữ chưa fine-tune tiếng Việt |

**Lưu ý khi đọc các con số**: mỗi model card đo theo cách khác nhau (khác tập
câu hỏi, khác chỉ số — Accuracy, MRR hay NDCG), và một số model đã thấy dữ liệu
Zalo Legal lúc huấn luyện. Các con số **không so sánh trực tiếp** được với nhau
và không thay thế được benchmark trên dữ liệu của dự án (mục 6).

### 2.2. Quyết định

**Mặc định triển khai: `AITeamVN/Vietnamese_Embedding`.**

- Kiến trúc encoder (BGE-M3), cộng đồng dùng rộng rãi, tài liệu đầy đủ, chạy
  trực tiếp bằng `sentence-transformers`.
- Dùng tokenizer subword riêng (XLM-RoBERTa), **không phụ thuộc** bước tách từ
  tiếng Việt — lỗi tách từ của BM25 không lan sang nhánh dense, hai nhánh bổ
  sung cho nhau tốt hơn.
- Không cần tiền tố/instruction cho query, cấu hình đơn giản nhất.
- Max 2048 token, dư nhiều so với chunk 512 token.

**Bắt buộc benchmark trước khi chốt** (mục 6) với hai ứng viên chuyên luật:
`darklethelong/vnlegal-lal` và `mainguyen9/vietlegal-e5`. Nếu một trong hai
vượt mặc định rõ rệt trên bộ đánh giá của dự án (Recall@20 cao hơn ≥ 3 điểm) mà
độ trễ vẫn đạt yêu cầu, chuyển sang model đó — chỉ cần đổi cấu hình và build
lại index, không đổi code.

**Mốc so sánh**: `bkai-foundation-models/vietnamese-bi-encoder` (nhỏ, nhanh) và
`BAAI/bge-m3` (chưa fine-tune) để biết fine-tune tiếng Việt mang lại bao nhiêu.

## 3. Chuẩn bị text

| | Văn bản (indexing) | Câu hỏi (query) |
|---|---|---|
| Text đưa vào model | `context_header + "\n" + content` | `question` |
| Chuẩn hóa | Unicode NFC (đã làm ở Data Processing Flow) | Unicode NFC, trim |
| Chữ thường | **Không** — model phân biệt hoa/thường, giữ nguyên | Không |
| Tách từ | Không (trừ khi dùng BKAI, khi đó tách bằng PyVi cho cả hai phía) | Như bên trái |
| Tiền tố | `passage_prefix` theo cấu hình (rỗng với model mặc định; `passage: ` với E5) | `query_prefix` theo cấu hình (rỗng / `query: ` / instruction tùy model) |

Tiền tố là cấu hình của từng model, khai báo trong `configs/retrieval.yaml`;
dùng sai tiền tố làm giảm chất lượng đáng kể mà không báo lỗi.

## 4. Chiến lược indexing vector

### 4.1. Collection Qdrant

```python
from qdrant_client import QdrantClient, models

client.create_collection(
    collection_name=f"legal_chunks_{index_version}",
    vectors_config={
        "dense": models.VectorParams(size=1024, distance=models.Distance.COSINE),
    },
)
for field in ["legal_status", "document_type", "document_id", "document_key"]:
    client.create_payload_index(collection_name, field, models.PayloadSchemaType.KEYWORD)
client.create_payload_index(collection_name, "effective_date", models.PayloadSchemaType.DATETIME)
client.update_collection_aliases(change_aliases_operations=[
    models.CreateAliasOperation(create_alias=models.CreateAlias(
        collection_name=f"legal_chunks_{index_version}", alias_name="legal_chunks"))
])
```

| Thành phần | Thiết lập | Lý do |
|---|---|---|
| Named vector | `dense` | Chừa chỗ thêm vector `bm25` (sparse) sau này mà không tạo collection mới |
| Khoảng cách | Cosine | Chuẩn của các model trong danh sách |
| Chuẩn hóa vector | L2-normalize trước khi upsert (`normalize_embeddings=True`) | Cosine = dot product, ổn định giữa các model |
| Point ID | `uuid5(NAMESPACE_URL, chunk_id)` | Qdrant yêu cầu số nguyên hoặc UUID; sinh xác định từ `chunk_id` nên upsert lại không tạo bản trùng |
| Payload | Toàn bộ metadata của chunk (Metadata Specification) | Truy vấn trả luôn metadata, không cần tra cứu thêm |
| Payload index | `legal_status`, `document_type`, `document_id`, `document_key`, `effective_date` | Lọc nhanh khi truy vấn |
| Chỉ mục ANN | HNSW mặc định (`m=16`, `ef_construct=100`) | Với vài nghìn chunk, Qdrant tự dùng full scan dưới ngưỡng `full_scan_threshold`, kết quả gần như chính xác tuyệt đối |
| Quantization | Không dùng | Corpus nhỏ, ưu tiên độ chính xác |

### 4.2. Quy trình build

```text
chunks.jsonl
  → lọc legal_status mặc định
  → ghép text (mục 3)
  → encode theo batch (batch_size = 32; fp16 nếu có GPU)
  → lưu cache: data/index/dense/{index_version}/embeddings.npy + chunk_ids.json
  → upsert Qdrant theo batch 256 point
  → kiểm tra: số point == số chunk; truy vấn thử 5 câu hỏi mẫu
  → chuyển alias legal_chunks sang collection mới
  → ghi index_manifest.json
```

- Cache embedding giúp build lại collection (đổi cấu hình HNSW, payload) mà
  không phải chạy lại model.
- Ghi vào `index_manifest.json`: tên model, **revision (commit hash) trên
  Hugging Face**, `query_prefix`, `passage_prefix`, số chiều. Model phải được tải
  theo revision cố định — nếu tác giả cập nhật model, vector cũ và mới không còn
  cùng không gian, kết quả sẽ sai âm thầm.
- Môi trường chạy dùng model đã tải sẵn (`HF_HUB_OFFLINE=1`), không tải lúc khởi động.

### 4.3. Truy vấn

```python
query_vec = model.encode(query_prefix + question, normalize_embeddings=True)
hits = client.query_points(
    collection_name="legal_chunks",
    query=query_vec,
    using="dense",
    limit=candidates,                         # 100 khi chạy hybrid, top_k khi chạy dense riêng
    query_filter=models.Filter(must=[
        models.FieldCondition(key="legal_status",
                              match=models.MatchAny(any=["con_hieu_luc", "het_hieu_luc_mot_phan"])),
    ]),
    with_payload=True,
)
```

- `score` trong output là cosine similarity (−1 đến 1); `retrieval_method = "dense"`.
- Dense luôn trả về đủ `limit` kết quả (luôn có vector "gần nhất"), kể cả khi
  câu hỏi không liên quan. Việc kết luận "không đủ căn cứ" thuộc reranker và
  LLM của Team 2; Team 1 **không** tự cắt theo ngưỡng cosine ở MVP vì ngưỡng
  phụ thuộc model và chưa được đo.

## 5. Tài nguyên

| Hạng mục | Ước tính với model mặc định |
|---|---|
| RAM nạp model (fp32) | ~2,5 GB |
| Encode một câu hỏi trên CPU | Vài chục đến vài trăm ms (cần đo trên máy triển khai) |
| Encode vài nghìn chunk lúc build | Vài phút trên CPU; dưới một phút với GPU |
| Dung lượng vector trong Qdrant | 4 KB / chunk (1024 × float32) — vài nghìn chunk chỉ khoảng chục MB |

Model nạp **một lần** khi khởi động `Retriever`, dùng lại cho mọi truy vấn.

## 6. Thử nghiệm

Trên bộ đánh giá chung (Retrieval Design mục 5), với cùng tập chunk:

| Đo | Mục đích |
|---|---|
| Recall@5, Recall@20, MRR@10 cho từng model ở mục 2.1 | Chọn model |
| p50 / p95 thời gian encode câu hỏi trên máy triển khai | Đảm bảo ngân sách độ trễ |
| Chất lượng theo nhóm câu hỏi: có số hiệu / diễn đạt đời thường | Biết model yếu ở đâu để hybrid bù |

Ghi lại tên model, revision, tiền tố, ngày chạy và cấu hình chunk trong kết
quả để có thể chạy lại.
