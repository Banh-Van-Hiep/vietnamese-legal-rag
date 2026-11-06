# Kế Hoạch Triển Khai Kỹ Thuật — Tuần 9
## Phân Hệ: RAG & LLM (Team 2)

Bản nháp, chưa có chữ ký của Người 1 và Người 2. Số liệu lấy từ `origin/develop` tại `fd52f6f` và báo cáo Tuần 8 (PR #47).

---

## 1. Thông Tin Chung & Mục Tiêu
- **Giai đoạn:** Tuần 9 (Tuần 6 cũ + 3), ứng với VLRA Sprint 6 trên Jira, từ 02/11 đến 09/11/2026.
- **Hạn:** cả ba ticket đến hạn 09/11/2026. Tính từ 04/11 chỉ còn 5 ngày, trong khi Dev Set chưa đóng băng và chưa có LLM chạy thật (xem mục 6). VLRA-68 là ticket dễ trễ nhất.
- **Mục tiêu:**
  - Viết lại System Prompt và Context Builder để LLM chỉ trả lời từ context được cấp, nêu điều kiện và ngoại lệ có trong nguồn, và từ chối khi thiếu căn cứ (VLRA-66).
  - Chuẩn hóa output của LLM thành JSON có `answer`, citation và `claims` để module Verification đọc được.
  - Ghép RAG Pipeline v2: Retrieval, Context Builder, LLM, Verification, rồi trả kết quả đúng contract với Team 3 (VLRA-67).
  - Viết Citation Verification và chạy benchmark trên Dev Set với Citation Correctness, Citation Coverage, Hallucination Rate (VLRA-67 nửa đầu, VLRA-68). Citation Correctness cần đạt ít nhất 90%.

### Hiện trạng trên code (tại 04/11, trước khi làm Tuần 9; trạng thái hiện tại ở mục 8)
- `answer.py` kiểm tra metadata citation có khớp chunk đã gửi cho LLM hay không, kiểm tra marker và citation hai chiều, rồi đánh lại nhãn `C1..Cn`. `pipeline.validate_generated_response` kiểm tra thêm định dạng marker. Cả hai chỉ chứng minh nguồn nhất quán với context. Chúng chưa kiểm tra nguồn có thật sự hỗ trợ kết luận (xem [citation-specification.md](../../../docs/team2_rag/citation-specification.md)).
- Prompt `prompt_v2` đã có nhánh `insufficient_context`. Hiện chỉ trường hợp context rỗng mới bị chặn trước khi gọi LLM.
- `parse_llm_output` chỉ nhận đúng ba key `status, answer, citations`, và contract với Team 3 không cho thêm field.
- `runtime.py` trên `develop` dùng `BGEScorer()` với `truncate=False`, `RAG_TOP_K=10`, `RAG_STRICT_RERANK=false`. Chưa có bộ hẹn giờ dừng rerank sau 4 giây.
- Mục "Hoàn thành nhiệm vụ Người 2 — 31/10/2026" trong [tasks Tuần 8](../week8/tasks.md) ghi runtime đã bật `truncate=True` và timeout 4 giây. Code hiện tại không như vậy, nên mục đó cần sửa (việc VLRA-T2-28).

---

## 2. Phân Rã Công Việc

Mã `VLRA-T2-NN` là mã nội bộ của Team 2, nối tiếp các tuần trước (Tuần 8 kết thúc ở VLRA-T2-17). Ba ticket Jira bên dưới đều thuộc Sprint 6, hạn 09/11/2026, nhãn Team2, 2 story point mỗi ticket, trạng thái To Do, chưa gán người (kiểm tra ngày 04/11/2026).

| Jira | Tên ticket | Epic | Mã nội bộ |
| :--- | :--- | :--- | :--- |
| VLRA-66 | Cập nhật System Prompt & Prompt Template | EPIC 3 Core RAG & LLM Engine | VLRA-T2-18 đến 21 |
| VLRA-67 | Xây dựng module Citation Verification và đóng gói RAG Pipeline v2 | EPIC 3 Core RAG & LLM Engine | VLRA-T2-22, 23 (Người 1) và VLRA-T2-24 (Người 2) |
| VLRA-68 | Đo lường chất lượng câu trả lời, Hallucination Rate và Citation Metrics trên Dev Set | EPIC 5 System Evaluation & Benchmark | VLRA-T2-25 đến 27 |

Jira chưa tách VLRA-67 thành phần của từng người và chưa có subtask. Cách chia theo người trong tài liệu này là đề xuất của nhóm.

### 2.1. Người 1: Core Pipeline & LLM Prompting (VLRA-66, nửa sau VLRA-67)

| Mã | Công việc | Tiêu chí hoàn thành (DoD) |
| :--- | :--- | :--- |
| VLRA-T2-18 | Chốt schema output nội bộ của LLM gồm `status`, `answer`, `citations`, `claims` (mỗi claim gắn `citation_ids`). Sửa `llm/output_parser.py`, `llm/types.py`, `docs/team2_rag/schemas/llm_output.schema.json` (bản hiện tại thiếu `status`) và FakeLLM. Gửi schema và fixture cho Người 2 trong 1 đến 2 ngày đầu. | Người 2 xác nhận schema và fixture dùng được. Test parser pass với output hợp lệ và các ca sai (thiếu claim, `citation_ids` trỏ nhãn lạ). Response gửi Team 3 vẫn là `status, answer, citations`, không lộ `claims`. |
| VLRA-T2-19 | Viết lại System Prompt trong `prompts/templates.py` và nâng `PROMPT_VERSION`. Prompt chỉ dùng LEGAL CONTEXT, nêu điều kiện và ngoại lệ khi nguồn có, không suy diễn hiệu lực, bỏ qua chỉ dẫn chèn trong câu hỏi, history hay đoạn truy xuất. Cập nhật [prompt-design.md](../../../docs/team2_rag/prompt-design.md). | Tài liệu prompt khớp code. Có test render prompt, test giữ nguyên tag và test không rò chỉ dẫn. Có bộ câu thử tay (điều kiện/ngoại lệ, câu mơ hồ, prompt injection) kèm kết quả. |
| VLRA-T2-20 | Fallback và refuse khi thiếu căn cứ. Giữ nhánh context rỗng, rà lại `_REFERENCE` (câu hỏi nhắc lượt trước), thêm cổng theo độ liên quan nếu có đủ dữ liệu hiệu chỉnh (xem Blocker 4). | Mọi nhánh từ chối trả `insufficient_context`, `citations=[]`, không marker. Mỗi nhánh có test, và không gọi LLM khi không cần. |
| VLRA-T2-21 | Chỉnh Context Builder trong `prompts/context.py`: nhãn ổn định, giữ nguyên metadata, ngân sách token theo [context-builder.md](../../../docs/team2_rag/context-builder.md). | Test ngân sách token pass. Contract `retrieval_output` không đổi. |
| VLRA-T2-22 | Ghép Pipeline v2 trong `pipeline.py` và `runtime.py`. Đặt tường minh trọng số `BM25:Dense`, `top_k`, `truncate`, `strict_rerank` và ghi vào log và report. Cưỡng chế timeout rerank 4 giây rồi lùi về thứ hạng Hybrid. Cho phép bật hoặc tắt rerank để so sánh. | Chạy đủ luồng với FakeLLM và Verification (giả hoặc thật). Test timeout: quá hạn thì lùi về Hybrid, phản hồi không bị sập. Cấu hình chạy thật khớp tài liệu cấu hình. |
| VLRA-T2-23 | API đúng contract Team 3: `POST /internal/v1/query` trả `status, answer, citations`, lỗi ánh xạ theo [rag-io-specification.md](../../../docs/team2_rag/rag-io-specification.md). Khi Verification không qua thì trả `CITATION_INVALID`, không tự bỏ citation để vá. Mã này ánh xạ sang HTTP 502 và mã công khai `UPSTREAM_INVALID_RESPONSE` (theo `errors.py` và đúng với VLRA-T2-10 ở Tuần 7). | Test contract bằng `contracts/v0.1/validate_public_contract.py` và test API. `/internal/v1/ready` phản ánh đúng trạng thái. |

### 2.2. Người 2: Verification Engine & Benchmark (nửa đầu VLRA-67, VLRA-68)

| Mã | Công việc | Tiêu chí hoàn thành (DoD) |
| :--- | :--- | :--- |
| VLRA-T2-24 | Viết module Citation Verification: tách từng claim và đối chiếu về chunk nguồn; kiểm tra ID văn bản và Điều/Khoản/Điểm trong citation có tồn tại trong context; viết rubric chấm ngữ nghĩa cho citation. Module này là lớp kiểm tra ngữ nghĩa đặt trên Citation Validator có từ Tuần 7 (VLRA-T2-10). Validator cũ vẫn lo marker, đánh lại nhãn và membership của context, nên không viết lại phần đó. Đặt ở `team2_rag/verification/` (tên đề xuất). | Có hàm đúng chữ ký ở mục 4, chạy được với fixture của VLRA-T2-18. Test cho claim được hỗ trợ, claim không có nguồn, citation trỏ nhầm Điều/Khoản và citation bịa. Rubric nằm trong tài liệu. |
| VLRA-T2-25 | Định nghĩa ba chỉ số (bản nháp ở mục 3.3) và xác nhận với Người 1. | Công thức, mẫu số và cách tính câu `insufficient_context` được ghi rõ. |
| VLRA-T2-26 | Chạy benchmark trên Dev Set và các edge case Team 1 bàn giao, xuất báo cáo gồm số tổng, số theo nhóm câu và danh sách ca lỗi. | Báo cáo có raw output, commit đã chạy, cấu hình và hash Golden. Chỉ số chưa đo ghi "chưa đo". Kết quả chưa chạy trên Dev đã đóng băng gắn nhãn `exploratory`. |
| VLRA-T2-27 | Phân tích ca lỗi và gửi Người 1 để chỉnh prompt khi Citation Correctness dưới 90%. | Ca lỗi được phân loại (nguồn sai, claim không có nguồn, prompt, retrieval). Mỗi đề xuất sửa có kèm lần chạy lại. |

### 2.3. Việc chung

| Mã | Công việc | DoD |
| :--- | :--- | :--- |
| VLRA-T2-28 | Sửa các mô tả sai trong tasks Tuần 8 (trạng thái `truncate` và timeout ở runtime). Giải quyết mâu thuẫn giữa [optimal_rag_configuration.md](../../../docs/team2_rag/optimal_rag_configuration.md) (đề xuất bật truncate) và kết luận giữ Hybrid làm mốc. | Hai người thống nhất một cấu hình và ghi vào tài liệu. |
| VLRA-T2-29 | Lấy Dev Set đã đóng băng từ Team 1 (xem Blocker 1). | Có `split: "dev"` và `relevant_unit_groups`, hash được ghi lại. |

---

## 3. Thiết Kế

### 3.1. Luồng Pipeline v2
```text
Câu hỏi + history -> validate_input -> Retrieval (Hybrid, Team 1)
   -> Rerank (timeout 4s, lùi về Hybrid) -> Context Builder (ngân sách token)
   -> LLM Generator -> parse output nội bộ (có claims)
   -> Verification (Người 2) -> gỡ claims -> RAGResponse {status, answer, citations}
```
Không có chunk dùng được, hoặc câu hỏi nhắc lượt trước mà không nêu rõ đối tượng, thì pipeline trả `insufficient_context` và không gọi LLM.

### 3.2. Nguyên tắc cho Prompt
- LLM chỉ dựa vào LEGAL CONTEXT của lượt hiện tại. HISTORY chỉ giúp hiểu câu hỏi.
- Mỗi nhận định pháp lý có marker `[Ck]` ngay sau. Điều kiện và ngoại lệ chỉ được nêu khi nguồn có.
- Thiếu căn cứ thì từ chối, không đưa kết luận.
- Metadata citation chép nguyên văn từ tiêu đề chunk. Prompt không bảo đảm được điều này nên hậu kiểm vẫn bắt buộc.

### 3.3. Định nghĩa ba chỉ số (VLRA-T2-25)

Người 1 rà soát `verification/metrics.py` và `verifier.py` ngày 06/11/2026. Bảng dưới là điều code đang tính, không phải bản nháp ban đầu:

| Chỉ số | Công thức trong code | Mốc |
| :--- | :--- | :--- |
| Citation Correctness | `valid_citations / total_citations` trên các câu `answered`. Citation hợp lệ khi nhãn có trong context, `chunk_id` khớp và `document_id`, `article_id`, `article` khớp chunk. | ít nhất 90% |
| Citation Coverage | `supported_claims / total_claims`. Claim `supported` khi mọi citation của nó hợp lệ và điểm từ vựng ở mức SUPPORTED hoặc PARTIAL. | ít nhất 85% |
| Hallucination Rate | Mức câu: số câu `answered` có ít nhất một claim không được hỗ trợ hoặc không `passed`, chia cho số câu `answered`. Mức claim: `(total_claims - supported_claims) / total_claims`. Mốc áp cho mức câu. | không quá 5% |

Mẫu số bằng 0 thì ghi "chưa đo", không gán 100%. Câu `insufficient_context` và câu `error` không nằm trong mẫu số của cả ba chỉ số; báo cáo ghi riêng số câu của hai nhóm này.

Bốn chỗ code lệch với định nghĩa trong tài liệu hoặc gây hiểu nhầm, cần Người 2 xác nhận hướng xử lý:
1. **Citation Correctness chỉ đo nguồn gốc, không đo hỗ trợ ngữ nghĩa.** Cờ `supports_claim` có tính nhưng không dùng. Phần kiểm nguồn gốc đã được `answer.py` chặn bằng `CITATION_INVALID` trước khi tới Verification, nên chỉ số này gần như luôn đạt trên câu đã qua chặn. Nếu muốn đo đúng ý "citation hỗ trợ claim", cần tính citation đúng khi hợp lệ và có ít nhất một claim trích nó được hỗ trợ.
2. **Coverage và Hallucination mức claim là cùng một con số** (`1 - coverage = hallucination mức claim`). Hai chỉ số này không độc lập.
3. **Hallucination mức câu tính cả lỗi nguồn gốc** (điều kiện `not passed`), còn `citation_rubric.md` mục 4.3 chỉ nói claim UNSUPPORTED hoặc CONTRADICTED.
4. **Câu `error` bị loại khỏi mẫu số**, nên timeout làm các tỷ lệ đẹp lên. Khi báo cáo phải nêu số câu `error` ngay cạnh các tỷ lệ.

Chưa có tỷ lệ từ chối đúng và sai: cần nhãn "nên từ chối" trong Golden. Phần hỗ trợ ngữ nghĩa do heuristic từ vựng chấm (xem `citation_rubric.md`), chưa có người chấm tay đối chiếu.

---

## 4. Giao Tiếp Giữa Các Module

Output nội bộ của LLM, không ra API:
```python
from pydantic import BaseModel

class Claim(BaseModel):
    claim_id: str            # "K1"
    text: str                # nhận định pháp lý bằng tiếng Việt
    citation_ids: list[str]  # ["C1", "C3"], phải nằm trong citations

class LLMOutputV2(BaseModel):
    status: str              # "answered" | "insufficient_context"
    answer: str              # có marker [Ck]
    citations: list[dict]    # 9 trường theo citation-specification.md
    claims: list[Claim]      # rỗng khi insufficient_context
```

Người 2 viết, Người 1 gọi:
```python
def verify_response(output: LLMOutputV2, context: BuiltContext) -> VerificationResult: ...

class VerificationResult(BaseModel):
    passed: bool
    claim_results: list[ClaimCheck]        # claim_id, supported: bool, reason
    citation_results: list[CitationCheck]  # citation_id, exists_in_context, supports_claim
```

Response gửi Team 3 giữ nguyên: `{"status", "answer", "citations"}`, mỗi citation đủ 9 trường. `claims` và điểm số không đi qua API.

Fixture mẫu cho Người 2:
```json
{
  "status": "answered",
  "answer": "Doanh nghiệp phải thông báo thay đổi nội dung đăng ký [C1].",
  "citations": [{"citation_id": "C1", "chunk_id": "...", "document_id": "...", "article_id": "dieu-...", "document_title": "...", "article": "...", "clause": null, "point": null, "source_url": "https://..."}],
  "claims": [{"claim_id": "K1", "text": "Doanh nghiệp phải thông báo thay đổi nội dung đăng ký.", "citation_ids": ["C1"]}]
}
```
ID và URL trong fixture là chỗ giữ chỗ. Fixture thật phải lấy từ chunk có trong Golden của Team 1.

---

## 5. Phụ Thuộc Giữa Các Bên

| Chiều | Hạng mục | Dùng để | Kênh |
| :--- | :--- | :--- | :--- |
| Người 1 gửi Người 2 | Schema `claims`, fixture (VLRA-T2-18) và chữ ký hàm Verification | Người 2 viết verifier song song bằng FakeLLM | PR nhỏ vào `develop` đầu tuần |
| Người 2 gửi Người 1 | `verify_response`, `VerificationResult`, báo cáo ca lỗi (VLRA-T2-27) | Ghép vào pipeline và chỉnh prompt | PR, báo cáo benchmark |
| Team 1 gửi Team 2 | Dev Set đã review và đóng băng (`split: "dev"`, `relevant_unit_groups`), edge case | Chạy VLRA-68 | `team1_data/golden/` |
| Team 2 gửi Team 3 | Xác nhận contract không đổi, thời gian tầng AI nằm trong ngưỡng NFR-07 | Backend giữ nguyên timeout hiện tại | `CONTRACT.md`, `.env` |

---

## 6. Blockers & Quyết Định Cần Chốt

| # | Vấn đề | Hậu quả | Hướng xử lý |
| :--- | :--- | :--- | :--- |
| 1 | Dev Set chưa đóng băng. 70/110 câu còn `draft_needs_legal_review`, chưa có `split` hay `relevant_unit_groups`. | Mốc 90% chưa dùng để nghiệm thu được. | Làm việc với Team 1 (VLRA-T2-29). Trong lúc chờ, gắn nhãn `exploratory`. |
| 2 | Hai file Golden lệch nhau: `team1_data/golden/golden_phase1.json` (đúng bộ đã đo) và `team2_rag/data/golden/golden_phase1_30cai.json` (sáu câu lệch trường, gồm `gold_016` và `gold_021`). | Test `test_imported_cases_unchanged_from_team2_source` có thể lỗi, và số liệu không so sánh được. | Thống nhất snapshot với Team 1, không tự chọn một bên. |
| 3 | Chưa chạy được LLM thật. Chưa xác nhận tên model Gemini, chưa có key, chưa có index BM25/Dense trên máy. `qwen2.5:3b` có thể không đạt 90%. | Không đo được benchmark thật. | Chốt model benchmark. Model nặng chạy trên Colab. |
| 4 | Cổng từ chối theo độ liên quan cần ngưỡng điểm rerank. | Ngưỡng phải hiệu chỉnh trên Dev Set nên phụ thuộc Blocker 1. | Giữ cơ chế context rỗng trước, thêm cổng sau khi có dữ liệu. |
| 5 | Hybrid đạt Recall@5 88,39% còn BGE truncate đạt 83,08% trên 110 câu (exploratory). | Chưa rõ Pipeline v2 có nên dùng reranker mặc định. | Làm bản so sánh có và không rerank (VLRA-T2-22), quyết định theo số đo. |
| 6 | `develop` mặc định BM25:Dense `0,5:1`, runner cũ vẫn ghi `1:1`. | Report ghi sai cấu hình. | Đặt tường minh và ghi vào report (VLRA-T2-22). |
| 7 | "Hỗ trợ ngữ nghĩa" khó tự động hóa hoàn toàn. | Hallucination Rate kém tin cậy. | Dùng rubric và chấm tay một mẫu để hiệu chỉnh. |
| 8 | Hạn 09/11/2026 của cả ba ticket, còn 5 ngày kể từ 04/11. VLRA-68 cần Dev Set, LLM và verifier đều sẵn sàng. | Nếu Dev Set chưa đóng băng kịp, báo cáo VLRA-68 chỉ là số `exploratory`. | Chốt Dev Set và model benchmark trong 1 đến 2 ngày đầu. Nếu vẫn thiếu, báo người giao việc xin dời hạn hoặc nghiệm thu từng phần, không đổi mốc 90%. |

Hai người cần trả lời:
1. `claims` do LLM tự khai hay verifier tự tách theo marker? LLM tự khai tốn thêm output token và dễ sai trên model nhỏ. Nên thử cả hai trên vài chục câu rồi chọn.
2. Model benchmark là gì, chạy ở đâu?
3. Pipeline v2 có bật reranker mặc định không?
4. Công thức chính thức của ba chỉ số, và cách tính câu `insufficient_context`.
5. Module Verification nằm ở đâu trong repo, và ai review PR của ai?

---

## 7. Kiểm Thử & Tái Lập
- Chạy Python từ thư mục chứa `team2_rag/`. Bộ test liên quan (chạy ở Git root):
  `.venv/bin/python -m pytest tests/test_eval_reranker.py tests/test_team2_reranker.py tests/test_team2_pipeline.py tests/test_team2_api.py tests/test_retrieval_reranker_contract.py tests/test_golden_phase1.py -q`
- Model nặng chạy trên Colab bằng `notebooks/reranker_evaluation_colab.ipynb`. Ô setup vẫn clone nhánh `feature/team2-rag`, nên đọc SHA nó in ra trước khi đo.
- Báo cáo chỉ ghi số đã chạy thật.

---

## 8. Trạng Thái Tại 05/11/2026

Nhánh `feature/team2-rag` tại `bfa89a9`. 94 test Team 2 pass, contract validator 76/76.

| Mã | Trạng thái | Bằng chứng hoặc việc còn lại |
| :--- | :--- | :--- |
| VLRA-T2-18 | Xong | Parser nhận `claims` tùy chọn, response gửi Team 3 vẫn chỉ có `status, answer, citations`. Đã chạy `claims` với Gemini thật (`gemini-3.1-flash-lite`), hai lần đều đúng schema. |
| VLRA-T2-19 | Xong | `prompt_v3` và [prompt-design.md](../../../docs/team2_rag/prompt-design.md). Bộ thử tay 7 ca chạy với LLM thật, 7/7 đạt. |
| VLRA-T2-20 | Xong một phần | Các nhánh từ chối có test và log lý do. Chưa có cổng từ chối theo điểm rerank vì chưa có Dev Set đóng băng để chọn ngưỡng (Blocker 4). |
| VLRA-T2-21 | Xong | Context Builder giữ nhãn và metadata, test ngân sách token pass. |
| VLRA-T2-22 | Xong một phần | Trọng số, `top_k`, `truncate`, rerank bật tắt và timeout 4 giây đều đặt tường minh và ghi vào log `rag_config`. Chưa có bản so sánh có và không rerank trên Dev Set. |
| VLRA-T2-23 | Xong | API đúng contract. `CITATION_INVALID` ánh xạ sang HTTP 502 và mã công khai `UPSTREAM_INVALID_RESPONSE`. |
| VLRA-T2-24 | Xong | `verify_response` 2 tầng chạy với output thật. Đã lập tài liệu rubric chính thức tại `docs/team2_rag/citation_rubric.md` (4 cấp độ ngữ nghĩa, ranh giới heuristic lexical-semantic). Test 7/7 pass. |
| VLRA-T2-25 | Người 1 đã rà soát, chờ Người 2 | `metrics.py` xử lý mẫu số 0 là "chưa đo" và tách hai mức Hallucination. Công thức ghi ở mục 3.3 theo đúng code, kèm bốn chỗ lệch cần Người 2 quyết định hướng sửa. |
| VLRA-T2-26 | Runner xong, chưa có lần chạy đủ | Runner chạy pipeline thật, có `--throttle`, checkpoint, ghi commit, hash Golden và cấu hình; benchmark tắt fallback Gemini và ghi model thật. Báo cáo hiện có mới 3 câu (0 câu `answered`), nên mọi chỉ số vẫn "chưa đo". Cần chạy đủ ít nhất 30 câu. |
| VLRA-T2-27 | Phân loại xong, chưa có dữ liệu để phân tích | Runner phân ca lỗi theo loại ngoại lệ: lỗi LLM như timeout là "hạ tầng LLM", không phải prompt. Chưa có lần chạy đủ nên chưa có ca lỗi thật để chỉnh prompt. |
| VLRA-T2-28 | Xong phần sửa tài liệu, chờ quyết định rerank | Đã sửa mô tả sai của Tuần 8 (`truncate` mặc định là `false`, timeout 4 giây mới có từ Tuần 9) và `optimal_rag_configuration.md`. Chưa chốt rerank mặc định bật hay tắt; cần bản so sánh trên Dev Set đã đóng băng và Người 2 xác nhận. |
| VLRA-T2-29 | Chờ Team 1 | Dev Set chưa đóng băng, hai file Golden còn lệch. |

Chạy thử cả hệ thống (Frontend, Backend, Team 2 API, Gemini) dùng `RAG_BM25_ONLY=true`, chỉ BM25 và không rerank, nên chất lượng truy xuất thấp hơn Hybrid và không dùng để đo benchmark. LLM đang dùng `gemini-3.1-flash-lite`, tên model chưa được Người 2 xác nhận.
