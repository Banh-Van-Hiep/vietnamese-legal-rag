# Tuần 3 — Kiểm thử retrieval, phối hợp Team 1

**Tiếp nhận:** 19/10/2026. **Người thực hiện:** thành viên Team 3 được giao kiểm thử Team 1.
**Quy ước lịch:** tuần triển khai 3 = tuần học phần 6, kế thừa cách đánh số tuần 2;
đây là nhãn tổ chức hồ sơ, không đổi thời hạn/trạng thái Jira.
**Baseline kiểm tra source:** `5a9af42e734391e00dfc0f7ede304506fdd5a28f` + tài liệu local chưa commit.

## 1. Nguồn nhiệm vụ

Hai nhiệm vụ dưới thuộc [VLRA-2](https://banhvanhiep.atlassian.net/browse/VLRA-2),
trạng thái **In Progress** theo nội dung người dùng cung cấp trong phiên này.
Không suy trạng thái từ code hoặc cập nhật Jira bằng tài liệu này.

| Jira | Mục tiêu đã giao | Đầu ra bắt buộc |
| --- | --- | --- |
| [VLRA-28](https://banhvanhiep.atlassian.net/browse/VLRA-28) — Kiểm thử BM25 Retrieval | Kiểm thử độc lập việc khởi tạo index, xử lý query và trả chunk phù hợp; dùng câu hỏi dựa trên corpus pháp luật hiện có | Bộ unit test BM25; kết quả Top-K/chunk_id; báo cáo pass/fail; danh sách lỗi phát hiện |
| [VLRA-29](https://banhvanhiep.atlassian.net/browse/VLRA-29) — Kiểm thử Dense và Hybrid Retrieval | Kiểm thử tạo embedding, truy vấn vector, hợp nhất RRF và thứ hạng chunk theo thiết kế | Bộ test Dense/Hybrid; kết quả embedding/similarity/RRF; chunk_id/dedup; báo cáo pass/fail và lỗi cần xử lý |

## 2. Phân công và ranh giới

Đây là nhiệm vụ **kiểm thử chức năng Team 1**, lưu hồ sơ theo người thực hiện tại
`specs/team3/week-03/`. Phân công này được người dùng xác nhận; không coi là Team 3
nhận quyền sở hữu toàn bộ data/retrieval hoặc được giao xây module Hybrid còn thiếu.

- Đặc tả chức năng lấy từ docs Team 1; contract chung lấy từ `contracts/v0.1/`.
  [Docs Team 3](../../../docs/team3_fullstack/README.md) cung cấp ranh giới tích hợp/grounding.
- Tái sử dụng test hiện có, bổ sung khoảng trống có căn cứ; không giao lại toàn bộ test
  như công việc chưa được viết. Có test không chứng minh đã chạy hoặc đã PASS.
- Không sửa production retrieval, corpus, metadata pháp lý, index đang phục vụ,
  Frontend/Backend hoặc code Team 2 để làm test đạt. Phát hiện lỗi phải có ca tái hiện
  và bàn giao owner; việc sửa production cần phạm vi/đặc tả riêng.
- Không thêm ngưỡng Recall/latency/coverage hoặc đổi model, schema, thuật toán khi chưa chốt.
  BM25/Dense/Hybrid cần phân biệt rõ phương pháp và score; điểm không là độ tin cậy pháp lý.

## 3. Căn cứ chức năng cần đọc

| Nguồn | Nội dung dùng cho nhiệm vụ |
| --- | --- |
| [Retrieval Design](../../../docs/team1_data/retrieval-design.md) §1/4/5 | Input/output, lỗi, snapshot/index và phân biệt kiểm thử chức năng với benchmark |
| [BM25 Proposal](../../../docs/team1_data/bm25-proposal.md) §3–4 | Chuẩn hóa query, cụm pháp lý, index, loại điểm 0 và phương pháp BM25 |
| [Dense Proposal](../../../docs/team1_data/dense-retrieval-proposal.md) §2–5 | Embedding/prefix, cosine, index/vector/metadata và phương pháp Dense |
| [Hybrid Proposal](../../../docs/team1_data/hybrid-retrieval-proposal.md) §4–5 | RRF, rank từ 1, dedup, tie-break, rỗng/lỗi từng nhánh |
| [Contract](../../../contracts/v0.1/CONTRACT.md), [Retrieval schema](../../../contracts/v0.1/retrieval_output.schema.json) | Payload hai field gốc, 12 field mỗi candidate, top_k, IDs/rank/method/provenance |
| [Grounding/integration Team 3](../README.md#3-quyết-định-kế-thừa-và-ranh-giới) | Không coi history/score/schema PASS là chứng minh hiệu lực hay hỗ trợ pháp lý |

Tài liệu Team 1 là nguồn thiết kế, code là hiện trạng. Khác biệt phải được ghi rõ;
không tự nâng hành vi code thành contract hoặc sửa tài liệu của Team 1/2.

## 4. Snapshot lúc tiếp nhận qua đọc source

Bảng dưới là inventory trước thực thi; kết quả kiểm thử cập nhật tại [verification.md](verification.md).

| Phần | Đã có | Khoảng cần đối chiếu tiếp |
| --- | --- | --- |
| BM25 | Module/tokenizer/persistence, 18 hàm test tại tests/test_bm25_retrieval.py | Test chủ yếu dùng fixture nhỏ; cần corpus thật, mapping câu hỏi–chunk, edge cases và bằng chứng chạy |
| Dense | Module/embedding adapter/Qdrant; 22 hàm test tại tests/test_dense_retrieval.py | Dùng FakeEmbedder + Qdrant in-memory; chưa là bằng chứng model thật hoặc chất lượng ngữ nghĩa |
| Hybrid | Thiết kế và phác thảo RRF trong docs | Chưa tìm thấy module Hybrid/RRF hoặc test runtime tương ứng trong nhánh hiện tại |

18/22 là số định nghĩa test đọc từ source, không phải test count/PASS. Test có thể skip
nếu thiếu dependency; skip không đủ điều kiện nghiệm thu. Các nhận định BM25/Dense
“chưa có implementation” trong hồ sơ tuần cũ không còn áp dụng cho source hiện tại.

## 5. Điều kiện bàn giao

Mỗi nhiệm vụ có ma trận yêu cầu → test/evidence; unit tests tái sử dụng/bổ sung được
chạy và báo đúng pass/fail/error/skip. Query corpus thật ghi snapshot/hash, question,
Top-K, expected chunk IDs cùng căn cứ nhãn, actual rank/score/IDs và nhận định rõ ràng.
Phần chưa có module/model/dependency ghi BLOCKED hoặc NOT RUN, không đổi thành PASS.

Lỗi được ghi theo nhóm nguyên nhân và ca tái hiện, kể cả không có lỗi sau khi đã chạy
thì ghi “không phát hiện trong phạm vi đã kiểm chứng”. Thiếu Hybrid là gap/dependency,
không kết luận thuật toán hỏng hoặc tự viết thuật toán thay owner.

Nghiệm thu **task → bằng chứng → VLRA-28/29 → tuần**; hai Jira độc lập về kết luận.
BM25/Dense có thể tiến hành khi Hybrid chưa sẵn sàng. Chưa nghiệm thu tuần 3 hoặc
chạy lại/đổi trạng thái tuần 2 từ lần tiếp nhận này.

## 6. Quy trình và tiến độ

Theo yêu cầu ngày 19/10, áp dụng [hướng dẫn tester](https://velvetforest.github.io/minh-hoa-BTL/minh-hoa-cong-viec.html): thêm evaluator, mixin contract, golden/nhóm riêng và benchmark model mặc định.
Hai bộ đã qua clarify → plan → tasks → analyze và sửa I1/U1 trước implement.
Tiến độ thực tế xem verification.md; không suy PASS từ spec hoặc source. Không sửa
production/contract/docs T1/T2, không commit/push.
