# Bàn giao kiểm thử Hybrid cho owner VLRA-27

Ngày 19/10, HEAD 5a9af42 chưa có runtime Hybrid/RRF/factory. Không triển khai thay owner.

## Interface và công cụ tái dùng
- retrieve(question, top_k=20) → {question, results}, contract v0.1, K1..50.
- Mixin: tests/retriever_contract.py, class RetrieverContractTests; concrete TestCase cấp retriever/method=hybrid_rrf/sample_question.
- Evaluator: scripts/eval_retrieval.py --method hybrid_rrf --factory owner_module:function;
  factory QA nhận argparse Namespace và trả retriever, không áp đặt factory production.
- Hai index cùng version/tập IDs; public K<=50 nhưng thiết kế candidate100 cần đường nội bộ
  do owner cung cấp. Chưa chốt tên/kiểu _search, tester không tự thêm hoặc nới contract.

## Case bắt buộc sau bàn giao
| Case | Expected |
| --- | --- |
| BM25[A,C,B,E], Dense[B,D,E,F,A], k60, weights1/1 | B,A,E,C,D,F; xem [oracle](../evidence/rrf-oracle.json) |
| B có rank3 và1 | 1/63+1/61, không cộng cosine/BM25 raw score |
| A có rank1 và5 | 1/61+1/65 |
| Hai nhánh[A,B] và[B,A] | Cùng score/best rank, lexical A trước B |
| ID có ở hai nhánh | Chỉ một row, hai đóng góp rank; rank output liên tục |
| Một nhánh success rỗng | Nhánh còn lại góp điểm; vẫn khác branch failure |
| Hai nhánh success rỗng | results=[] |
| Một nhánh exception | Raise lỗi, không trả single-branch với nhãn hybrid |
| Vượt timeout5s cấu hình | Timeout observably, không giả results=[] |
| Index version hoặc tập IDs lệch | Từ chối chạy |
| Metadata cùng ID lệch, ID trùng trong một nhánh | Báo vi phạm input/integrity; không double count |
| Benchmark cùng snapshot/golden/model | Recall20>=0.90 và không dưới nhánh tốt nhất; báo nhóm và latency |

Oracle chỉ xác nhận phép tính tham chiếu. Toàn bộ case runtime trên vẫn BLOCKED,
không gán Hybrid PASS bằng test công thức, fake module hoặc test bị skip.
