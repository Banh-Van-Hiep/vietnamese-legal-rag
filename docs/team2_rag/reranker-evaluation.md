# Đánh giá Hybrid và Reranker

Phần Người 1, Team 2: VLRA-54 so sánh Hybrid với Hybrid + Reranker;
VLRA-55 đo thay đổi chất lượng, độ trễ và chỉ ra các ca cần xem lại.
Kết quả là đầu vào cho Người 2 tổng hợp VLRA-58. Không sửa retrieval,
Reranker, Context Builder hay API sản phẩm trong thay đổi này.

Đối chiếu kế hoạch và đặc tả mục 10.2 ngày 30/10/2026:

- [Kế hoạch triển khai](https://docs.google.com/document/d/18gVwtMctxmmrZ5h1dFkI_tmLnAj__vfDXAUHTiYUrl4/edit).
- [Đặc tả tổng thể](https://docs.google.com/document/d/1uDCSGNfzWXIaCSdggRrxcSuRREJ3StS278r4vZWNYPM/edit).

## Cách đo

Mỗi câu gọi Hybrid đúng một lần, lấy tối đa 20 ứng viên. Một nhánh giữ
thứ tự Hybrid, nhánh còn lại dùng `rerank_with_details(strict=True)` với
BGE mặc định: CPU, batch 2, tối đa 512 token/cặp. Không cắt ngầm passage,
không dùng fallback khi reranker lỗi. Metadata và điểm retrieval giữ nguyên;
điểm BGE lưu riêng. Top 5 chỉ là ngưỡng đánh giá, chưa qua Context Builder.

Recall@5/@10/@20 tính theo nhóm subchunk tương đương của cùng đơn vị
pháp lý; MRR@20 dùng vị trí gold hit đầu tiên. Macro-average trên câu
answerable, cùng các cặp chạy thành công. Câu insufficient_context không
vào mẫu số Recall/MRR. Lỗi được giữ trong JSON, có failure rate và exit
code khác 0; không dùng một run có lỗi để xác nhận đạt mục tiêu.

`promoted` là câu có thêm nhóm đúng trong top 5; `demoted` là câu mất nhóm
đúng; `mixed` vừa thêm vừa mất; `unchanged` không đổi nhóm được chạm.
Các tỷ lệ dùng cùng mẫu số cặp answerable thành công. Nhóm mất khỏi top 5
và nhóm vốn thiếu từ Hybrid top 20 được lưu riêng để review. Đây là dấu hiệu
định lượng, chưa đủ kết luận nguyên nhân như hiểu sai thuật ngữ hay sai hiệu lực.

Rerank không đổi candidate pool nên Recall@20 phải giữ nguyên khi cả hai
nhánh thành công. Tác động chủ yếu thể hiện ở Recall@5/@10 và MRR@20.
Không yêu cầu kết quả phải tăng để coi runner chạy đúng.

## Chạy test trên máy nhẹ

Tại thư mục gốc repo:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install 'jsonschema[format]>=4.25,<5'
.venv/bin/python -m unittest \
  tests.test_eval_reranker tests.test_eval_retrieval tests.test_team2_reranker -q
```

Test dùng scorer/retriever giả để kiểm chứng phép đo và xử lý lỗi.
Không tải model, không tạo index, không gọi LLM.

## Chạy thực nghiệm trên máy đủ tài nguyên

Cần index BM25/Dense có cùng version và tập chunk IDs với corpus,
Qdrant đã chứa collection tương ứng, embedding model và BGE. Có thể dùng
máy khác; không cần chạy Java, React hoặc Ollama. Cài các extras hiện có:

```bash
.venv/bin/python -m pip install -e '.[test,retrieval,dense,reranker,api]'
```

Dùng Dev đã được nhóm review và đóng băng. Mỗi mẫu giữ schema Golden hiện
có và bổ sung `split: "dev"`, `relevant_unit_groups: [["chunk-a", "chunk-a-sub"], ["chunk-b"]]`.
Ví dụ này chỉ mô tả định dạng; IDs phải có thật. Các phần tử cùng một nhóm
là những subchunk tương đương, không gom các Khoản khác nhau chỉ để tăng recall.
Runner từ chối Test Set, nhóm trùng, ID lạ hoặc nhóm không phủ gold_chunk_ids.
Việc review relevance và xác nhận đóng băng vẫn do nhóm thực hiện trước khi chạy.

```bash
.venv/bin/python -m scripts.eval_reranker \
  --golden /path/to/frozen-dev.json \
  --chunks data/doanh-nghiep/processed/chunks.jsonl \
  --bm25-index data/index/bm25/week4-local-v1 \
  --dense-index data/index/dense/week4-local-v1 \
  --qdrant-path data/index/qdrant-week4-local-v1 \
  --output ../work/reranker-dev.json
```

Đổi đường dẫn theo snapshot được bàn giao. Nếu dùng Qdrant server, thay
`--qdrant-path` bằng `--qdrant-url http://localhost:6333`. Không chạy đồng
thời tiến trình khác giữ cùng Qdrant local path.

Với Golden cũ chưa split, chỉ dùng `--exploratory` để khảo sát. Khi chưa có
gold group review, mỗi gold chunk được tính như một nhóm riêng; số đo đó
không thay benchmark theo nhóm tương đương. Không tự chia lại Golden đã
được dùng tối ưu thành Test độc lập.

Runner sinh JSON và Markdown cùng tên. Exit 0 là chạy đủ, 1 là có lỗi ở
câu, 2 là bị chặn khi chuẩn bị. JSON ghi commit/dirty state, hash corpus,
Golden, source, manifest index, version phụ thuộc và revision BGE thực tế
nếu model cung cấp. Giữ cả manifest/review record gốc cùng báo cáo khi bàn giao.

Setup tải/nạp model và warm-up được tách khỏi latency từng câu. Retrieval
warm-up một lượt bằng câu đầu, BGE warm-up bằng một cặp ngắn. Báo p50/p95
retrieval, rerank và tổng xử lý thành công; thời gian lỗi nằm ở từng câu.
Không nới timeout retrieval 5 giây. Tổng này chưa gồm Context Builder/LLM,
không chứng minh deadline Python 45 giây hay nghiệm thu E2E.

## Trạng thái kiểm chứng

Code nền: `develop` tại `eea5604`. Ngày 30/10/2026, bộ test liên quan chạy
37 test đạt. Đây là kiểm thử offline, chưa phải chạy model thật.

Golden hiện có 40 câu answered, chưa có split và relevant_unit_groups.
Lượt CLI exploratory với đường dẫn index lịch sử dừng ở thiếu
`data/index/bm25/week4-local-v1/index_manifest.json`, exit 2.
Chưa có Recall/MRR hoặc latency model thật để kết luận tác động Reranker.
Không tải model hay build index trên máy hiện tại vì người dùng cho biết máy yếu.

Người 2 dùng raw candidates, scores và các ca mất nhóm đúng để phân tích
nguyên nhân trong VLRA-56/57. Chưa chốt cấu hình tối ưu VLRA-58 và chưa
đánh giá chất lượng answer/citation hoặc B0/T0 toàn hệ thống.
