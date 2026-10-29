# Validation — T3-13 Golden split

**Ngày kiểm chứng:**30/10/2026. **Kết quả:** công cụ hoàn tất; chờ bộ150 câu để chia thật.

## Expected / Actual

| Tiêu chí | Kết quả |
| --- | --- |
| FR001–004:150→90/60, phân tầng, bảo toàn/tái lập | PASS trên fixture150;112/38→Dev67/23,Test45/15;113/37→Dev68/22,Test45/15; giữ ID/field bổ sung, đảo input không đổi2 tập, đổi seed đổi kết quả |
| FR005: SHA256/seed/phân bố/split_only | CLI end-to-end PASS; hash input và2 file khớp bytes; report không có phê duyệt hoặc manifest freeze |
| FR006: lỗi/no-overwrite/rollback | PASS size/duplicate ID/câu hỏi/type/enum/NFC/chunk logic/JSON duplicate key/NaN; bảo toàn file có sẵn và rollback khi lỗi ghi |
| Nguồn thật150 | Chưa chạy: repo hiện50 mẫu; CLI exit2, không tạo thư mục/file chia tập thật |

## Kiểm thử

13/13 test đạt trên Python3.12.15:

- Chia đúng90/60; phân tầng112/38 hoặc113/37 theo làm tròn.
- Giữ nguyên record/field bổ sung, không mất/trùng ID giữa2 tập.
- Cùng seed cho cùng kết quả, kể cả đảo thứ tự input.
- SHA-256 nguồn/output khớp; output có sẵn được bảo vệ, ghi lỗi được rollback.
- Từ chối size/duplicate/type/enum/NFC/chunk logic/JSON không hợp lệ.

Bộ thật hiện50 bị từ chối đúng exit2, chưa có Dev/Test thật.

## Bằng chứng và bàn giao

Bằng chứng tại `backend/target/final-acceptance-20261030/`.

1. **Team1:** bổ sung đủ150 câu.
2. **Team2:** kiểm chứng bộ nguồn.
3. **Team3:** chạy tool, bàn giao90 Dev/60 Test và split report có seed/phân bố/SHA-256.

[Tool](../../../tools/split_golden_dataset.py) · [Tests](../../../tests/test_split_golden_dataset.py) ·
[Tasks](tasks.md) · [Nghiệm thu tuần7](../verification.md).
