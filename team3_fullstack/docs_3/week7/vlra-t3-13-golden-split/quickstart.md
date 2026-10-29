# Quickstart — chia Golden150 thành90 Dev/60 Test

Chỉ chạy sau khi Team1 bàn giao đủ150 và Team2 kiểm chứng nội dung. Từ gốc repo:

```powershell
python -X utf8 team3_fullstack/tools/split_golden_dataset.py --input team2_rag/data/golden/golden_dataset_v1.json --output-dir team2_rag/data/golden --seed 20261029
```

Đường dẫn input là ví dụ bàn giao tương lai, hiện chưa có file v1 này. Có thể truyền
file150 khác được nhóm chốt. Tool không sửa input. Output3 file:
golden_dataset_v1.dev.json, golden_dataset_v1.test.json, golden_dataset_v1.split.json.
Đây là chia tập, không phải freeze; report ghi split_only và phân bố thực tế.
Nếu output đã có, dùng folder mới để đối chiếu; không có tùy chọn ghi đè ngầm.

```powershell
python -X utf8 -m unittest discover -s team3_fullstack/tests -p test_split_golden_dataset.py -v
```

Exit0 thành công; exit2 do đầu vào/ghi file không hợp lệ. BộPhase1 hiện50 phải bị
từ chối, không xuất Dev/Test thật. Mẫu test kỹ thuật150 chỉ ở temp, không phải Golden.
