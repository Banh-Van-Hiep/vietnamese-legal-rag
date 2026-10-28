# Kiểm chứng public contract

Chạy từ gốc repository với Python đã có jsonschema; không cần API key/LLM.

```powershell
python -X utf8 contracts/v0.1/validate_public_contract.py
```

Expected: schema hợp lệ, mọi ca positive đạt, ca negative bị từ chối, exit 0.
Đối chiếu wire thật từ test HTTP hiện có bằng JDK25/Maven Wrapper:

```powershell
cd team3_fullstack/backend
.\mvnw.cmd -B -ntp -Dtest=StreamApiTests test
cd ../..
python -X utf8 contracts/v0.1/validate_public_contract.py --wire-file team3_fullstack/backend/target/vlra41-contract-examples.json
```

Expected: request/meta/delta/complete thực được kiểm; binding/marker/citation đúng.
Đây là Java HTTP + upstream fixture, không phải RAG/LLM thật. Validator lỗi/missing file
phải exit khác 0. Ghi lệnh, counts, hash preservation/privacy/link checks tại validation.md.
Không chạy schema mới để sửa dữ liệu legacy; không chạy --wire-file trên file cũ rồi
báo đã thực hiện HTTP test mới. Không sửa test source chỉ để xuất thêm fixture.
