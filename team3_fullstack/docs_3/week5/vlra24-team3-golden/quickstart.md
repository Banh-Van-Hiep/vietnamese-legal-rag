# Quickstart — Golden Dataset chung

Từ gốc repository:

```powershell
python -X utf8 team2_rag/validate_golden.py
```

Expected:50 mẫu, exit0. File mặc định:
`team2_rag/data/golden/golden_phase1_30cai.json`. Không cần override hoặc script riêng
Team3. PASS kiểm field/ID/status/chunk; [validation](validation.md) ghi kiểm bổ sung
và rà ý định. Chưa thay review pháp lý/cơ cấu. Không cần build FE/BE khi chỉ đổi dữ liệu.
