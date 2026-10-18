# Reranker prototype — hướng dẫn tích hợp

## Phạm vi

Module `team2_rag/reranker.py` nhận kết quả Hybrid Retrieval, chấm các cặp
`question/content` rồi chuyển toàn bộ pool đã xếp lại cho Context Builder.
Không gọi LLM, không thay `query()` mock và không triển khai retrieval của Team 1.

```python
from team2_rag.reranker import rerank

# retrieve do Team 1 cung cấp; generate_answer do người 2 cung cấp.
retrieval = retrieve(question, top_k=20)
reranked = rerank(retrieval)
response = generate_answer(reranked, history=history)
```

`generate_answer` hiện nằm trên nhánh `feature/team2-rag`; phần reranker không
import module đó nên có thể phát triển, kiểm thử riêng trên `develop`.

## Interface và trách nhiệm

Input có đúng `question`, `results`, theo
`contracts/v0.1/retrieval_output.schema.json`. Input phải có rank liên tục 1..N,
ID duy nhất và điểm retrieval hữu hạn; sai input phát sinh `RerankInputError`.

Output vẫn có `question`, `results`. Danh sách xếp theo điểm model giảm dần,
bằng điểm thì theo rank retrieval. Mỗi candidate giữ nguyên cả 12 trường:
`chunk_id`, `document_id`, `article_id`, `content`, `document_title`, `article`,
`clause`, `point`, `source_url`, `score`, `rank`, `retrieval_method`.

**`rank` vẫn là rank retrieval gốc. Context Builder phải duyệt thứ tự danh sách,
không sort lại bằng `rank`.** Không đổi `retrieval_method` thành `rerank`,
không thêm điểm rerank vào candidate. Schema trường vẫn tương thích retrieval,
nhưng quy tắc thứ tự danh sách sau rerank thuộc nội bộ Team 2.

Không cắt pool xuống 5: Context Builder của người 2 chọn tối đa 5 chunk theo
budget. Output là bản sao độc lập; không sửa object input.

Để lấy điểm và trạng thái fallback phục vụ test/đo đạc:

```python
from team2_rag.reranker import rerank_with_details

details = rerank_with_details(retrieval)
reranked = details.output
scores_by_chunk_id = details.scores
fallback_reason = details.fallback_reason
```

## Kiểm thử offline, không tải model

```bash
python -m pip install -e ".[test]"
python -m unittest discover -s tests -p 'test_team2_reranker.py' -v
python -m unittest discover -s tests -p 'test_team2_mock.py'
python -m team2_rag.reranker team2_rag/data/samples/reranker_input.json --mock
```

Demo mock dùng điểm giả 0, 1, 2 để đảo thứ tự 3 → 2 → 1; không đánh giá chất
lượng truy hồi. Fixture ghi rõ là dữ liệu giả, không dùng làm Golden Dataset.

## Chạy BGE thật

```bash
python -m pip install -e ".[test,reranker]"
python -m team2_rag.reranker team2_rag/data/samples/reranker_input.json --strict
```

Lần đầu tải model `BAAI/bge-reranker-v2-m3` từ Hugging Face; cần mạng, bộ nhớ
và dung lượng lưu model. Model chạy CPU, batch size 2, FP32 mặc định để dễ
kiểm tra trên Mac Apple Silicon. Module import và input rỗng không tải model.
Adapter theo ví dụ Transformers chính thức trong
[model card BAAI](https://huggingface.co/BAAI/bge-reranker-v2-m3#using-huggingface-transformers).
Không cần API key LLM.

Giới hạn prototype là 512 token cho cả cặp có special tokens. Không cắt ngầm
điều luật: một cặp vượt giới hạn thì cả pool dùng fallback retrieval. Người
triển khai có thể dùng `BGEScorer(batch_size=1)` nếu cần giảm bộ nhớ.

Mặc định model lỗi, thiếu dependency, sai số lượng/giá trị điểm hoặc input quá
dài: trả nguyên thứ tự retrieval, `scores={}`, ghi log loại lỗi an toàn.
Không che lỗi input hoặc lỗi retrieval ở bước trước. `strict=True` phát sinh
`RerankModelError`, dùng khi smoke test để không nhầm fallback với model chạy
thành công. Chế độ CLI bọc output trong thông tin chẩn đoán; hàm `rerank()`
chỉ trả payload `question/results` như interface đã chốt.

## Giới hạn và nghiệm thu

- Unit test dùng scorer/tokenizer/model giả; không chứng minh model thật đã
  tải/chạy thành công hoặc retrieval đã cải thiện.
- Chưa benchmark nDCG/MRR, Recall hoặc p50/p95 trên Golden Dataset. Khi có
  retrieval thật, đo cùng candidate pool và so baseline không rerank.
- Chưa có hard timeout 5 giây cho inference hoặc tải model. Muốn bảo đảm
  deadline cần worker/process có quản lý vòng đời; không coi fallback là
  cơ chế ngắt một model đang chạy. Khởi động và warm up trước khi phục vụ.
- Điểm model là mức liên quan, không phải xác suất câu trả lời pháp lý đúng.
- Trước bàn giao: chạy offline tests, smoke test thật với `--strict`, lưu
  cấu hình model/dependency và kết quả thực tế. Không ghi smoke test Done khi
  chỉ chạy demo `--mock`.
