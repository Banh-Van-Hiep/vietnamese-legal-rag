# Bàn giao và chạy lại sau sửa

## 1. Phần cần owner phản hồi

- Dense (VLRA-26): xem [D-01..D-03](002-vlra-29-dense-hybrid-tests/issues.md), gửi PR/commit sửa và quyết định đối chiếu prefix, physical point/chunk mapping, chuẩn hóa vector cực trị. Không đổi expected test chỉ để PASS.
- Hybrid (VLRA-27): xem [handoff](002-vlra-29-dense-hybrid-tests/hybrid-handoff.md), cung cấp runtime/factory, interface lấy candidate100 nội bộ, cấu hình timeout và version/index/model. Public K vẫn 1..50.
- Chạy Dense thật cần máy đủ RAM, model revision và Qdrant server/version thống nhất; FakeEmbedder + memory chỉ xác minh cơ chế.

Chưa có bản sửa được cung cấp tại thời điểm bàn giao v1.0. Trạng thái D-01..D-03
giữ OPEN, T005/T007 giữ BLOCKED. Không tạo kết quả v1.1 trước khi chạy lại thật.

## 2. Chuẩn bị môi trường mới

Chạy từ repository root, Python 3.12. Môi trường cũ được ghi trong verification;
không giả định máy người nhận có sẵn đường dẫn venv của lần chạy trước.

```powershell
py -3.12 -m venv .local/retrieval-qa-venv
$py = '.local/retrieval-qa-venv/Scripts/python.exe'
& $py -m pip install -e '.[retrieval,test]' numpy 'qdrant-client>=1.12,<2'
```

Lệnh trên đủ cho unit với model giả/memory, không tải model thật. Đối chiếu phiên bản
đã dùng trong evidence trước khi so sánh; ghi dependency thực tế nếu môi trường khác.
Chỉ cài extra dense/tải weights khi môi trường benchmark đã sẵn sàng.

## 3. Retest Dense sau khi nhận commit sửa

Ghi SHA của source sửa, SHA của bộ test, diff production, thời điểm và môi trường.
Giữ nguyên evidence v1.0. Dùng thư mục output mới cho mỗi SHA, không ghi đè evidence cũ.

```powershell
$fixSha = (git rev-parse HEAD).Trim()
$runDir = ".local/retrieval-retest/$fixSha"
& $py scripts/run_retrieval_tests.py --pattern test_retrieval_edge_cases.py --output-dir "$runDir/edge"
# Exit 1 vẫn là FAIL/ERROR cần đọc JSON/log; không bỏ qua để tuyên bố đạt.
& $py scripts/run_retrieval_tests.py --pattern test_dense_retrieval.py --output-dir "$runDir/dense"
& $py scripts/run_retrieval_tests.py --output-dir "$runDir/retrieval"
```

Đối chiếu ba test tái hiện trong issues với trạng thái mới; chỉ đóng từng D khi assertion
và test liên quan đạt, không SKIP/expectedFailure. Chạy lại regression toàn `tests/`
nếu diff chạm pipeline chung; R-P01 phải báo riêng nếu chưa được sửa.

## 4. Retest Hybrid khi có runtime

Nhận factory QA từ owner trước khi gọi evaluator; không tự giả lập runtime bằng oracle.
Chạy contract, RRF/dedup/tie-break/version/error/timeout trong handoff rồi benchmark
BM25, Dense và Hybrid cùng corpus/golden/model/index version. Lưu actual rank, score,
chunk_id, metric theo nhóm và latency. Mẫu insufficient_context báo riêng.
Nếu module, server hoặc tài nguyên còn thiếu, ghi BLOCKED và nguyên nhân.

## 5. Xuất biên bản tiếp theo

1. Lưu JSON/JUnit/log/source hashes mới tại `evidence/retests/<fix-sha>/`; không thay evidence v1.0.
2. Cập nhật từng lỗi bằng bảng trước/sau và tham chiếu test ID, fix SHA, evidence mới.
3. Xuất `reports/v1.1/bien-ban-kiem-thu.{md,pdf,docx}` khi đã chạy lại; giữ mục chính của v1.0, gồm testcase, luồng dữ liệu và giới hạn kiểm chứng.
4. Ghi ngày xuất thực tế, lịch sử sửa đổi, các mục còn BLOCKED và người review chưa xác nhận. Không đổi toàn bộ tuần thành PASS chỉ vì ba lỗi Dense đã sửa.
5. Đưa phiên bản mới qua PR và gắn link PR/PDF mới vào VLRA-28/29; không tự merge hoặc thay trạng thái Jira khi chưa nghiệm thu.
