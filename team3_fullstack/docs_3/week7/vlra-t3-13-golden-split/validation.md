# Validation — T3-13 Golden split

**Ngày:**29/10/2026. [Spec](spec.md), [plan](plan.md), [tasks](tasks.md),
[analyze](analysis.md). Phạm vi theo xác nhận mới: Team1 bổ sung150, Team2 kiểm chứng,
Team3 chỉ chia90 Dev/60 Test; không tự tạo/review/freeze Golden.

## Expected / Actual

| Tiêu chí | Kết quả |
| --- | --- |
| FR001–004:150→90/60, phân tầng, bảo toàn/tái lập | PASS trên fixture150;112/38→Dev67/23,Test45/15;113/37→Dev68/22,Test45/15; giữ ID/field bổ sung, đảo input không đổi2 tập, đổi seed đổi kết quả |
| FR005: SHA256/seed/phân bố/split_only | CLI end-to-end PASS; hash input và2 file khớp bytes; report không có phê duyệt hoặc manifest freeze |
| FR006: lỗi/no-overwrite/rollback | PASS size/duplicate ID/câu hỏi/type/enum/NFC/chunk logic/JSON duplicate key/NaN; bảo toàn file có sẵn và rollback khi lỗi ghi |
| FR007: ranh giới/shared data | Phase1, corpus và validator Team2 giữ nguyên SHA256; không sửa app/schema/team khác hoặc thêm dependency |
| Nguồn thật150 | Chưa chạy: repo hiện50 mẫu; CLI exit2, không tạo thư mục/file chia tập thật |

## Kiểm thử

```powershell
python -X utf8 -m unittest discover -s team3_fullstack/tests -p test_split_golden_dataset.py -v
```

13 test PASS trên Python3.14.8 và13 test PASS trên Python3.12 của môi trường dự án
(cùng13 ca, không cộng thành26 ca khác nhau). Các fixture kỹ thuật chỉ tạo trong
TemporaryDirectory, không phải QA pháp luật và không được đưa vào Golden chung.

Lần chạy sandbox đầu không thao tác được TemporaryDirectory trên Windows; đã giữ
logs lỗi môi trường, chạy lại với quyền thực thi kiểm thử và temp riêng trong target
thì13/13 đạt. Không sửa test hoặc bỏ case để che lỗi; không tải dependency/mạng.

Thử bộ thật hiện tại:

```powershell
python -X utf8 team3_fullstack/tools/split_golden_dataset.py --input team2_rag/data/golden/golden_phase1_30cai.json --output-dir team3_fullstack/backend/target/t3-13-golden-split-20261029/real-input-rejection
```

Expected/actual: exit2, yêu cầu đúng150 nhưng có50; không sinh output, không ghi đè
file chung. Không tạo golden_dataset_v1.dev/test/split trong thư mục Team2 ở lượt này.

## Evidence và bàn giao

Evidence ignored: backend/target/t3-13-golden-split-20261029/ gồm tests.log,
tests-python312.log, current-input.log, summary.json, preservation.json và các log
sandbox-temp trước khi chạy lại. Lệnh chạy nguồn150 tại [quickstart](quickstart.md).
Không chạy Maven/FE vì chỉ thêm công cụ stdlib Team3, không đổi application/config.

Công cụ hoàn tất trong phạm vi đã chốt; T008 còn chờ Team1/2 bàn giao150 để thực hiện
phân chia thật. Tool kiểm cấu trúc cơ học; không chứng minh chunk tồn tại, đúng luật,
không trùng ý diễn đạt hoặc dữ liệu đã được duyệt. Không đổi nhãn/tỷ lệ đầu vào,
không coi split report là freeze. Không tự commit/push.

Kiểm bàn giao: 19 file Markdown/49 tham chiếu local không lỗi; diff --check
PASS. T001–T007 hoàn thành; T008 giữ mở vì chưa có bộ150 thật.
