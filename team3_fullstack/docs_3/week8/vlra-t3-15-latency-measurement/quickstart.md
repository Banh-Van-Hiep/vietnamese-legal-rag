# Quickstart — T3-15

Từ gốc repo, Python3.12, cài riêng công cụ:

```powershell
python -m pip install -r team3_fullstack/requirements-performance.txt
python -m unittest discover -s team3_fullstack/tests -p "test_*latency*.py" -v
```

## Stack mock để thử công cụ

Dùng database PostgreSQL test riêng đã tạo sẵn; không dùng DB nghiệp vụ. Python chạy
mock cần extras api của repository (`python -m pip install -e ".[api,test]"`).

Terminal1 ở gốc repo:

```powershell
$env:RAG_MOCK_SCENARIO="answered"
python -m uvicorn team2_rag.api.mock_app:create_mock_app --factory --host 127.0.0.1 --port 8001
```

Terminal2 dùng JDK25, từ `team3_fullstack/backend`; thay URL/user bằng database test đã tạo:

```powershell
$env:SPRING_PROFILES_ACTIVE="rag"
$env:SPRING_DATASOURCE_URL="jdbc:postgresql://127.0.0.1:5432/legal_rag_benchmark"
$env:SPRING_DATASOURCE_USERNAME="legal_rag"
$env:SPRING_DATASOURCE_PASSWORD="<test database password>"
$env:RAG_BASE_URL="http://127.0.0.1:8001"
$env:CHAT_LATENCY_ENABLED="true"
New-Item -ItemType Directory -Force target | Out-Null
.\mvnw.cmd spring-boot:run "-Dspring-boot.run.jvmArguments=-Duser.timezone=UTC" *> target/performance-backend.log
```

Không thêm biến rag vào backend/.env qua run-local.ps1 legacy: script đó chỉ hỗ trợ
mock cũ. Dừng các process bằng Ctrl+C sau khi đo.

Terminal3 ở gốc repo, Python có dependency performance. Tạo20 record fixture trong target
(không là Golden thật):

```powershell
New-Item -ItemType Directory -Force team3_fullstack/backend/target/performance-smoke | Out-Null
$cases=1..20 | ForEach-Object { @{ id="smoke-$_"; question="Kiểm thử độ trễ mock $_" } }
$json=$cases | ConvertTo-Json -Depth 4
[IO.File]::WriteAllText((Join-Path (Get-Location) 'team3_fullstack/backend/target/performance-smoke/input.json'), $json, [Text.UTF8Encoding]::new($false))
python team3_fullstack/tools/measure_latency.py --mode mock --dataset team3_fullstack/backend/target/performance-smoke/input.json --base-url http://127.0.0.1:8080 --users 1 --warmup 1 --timing-log team3_fullstack/backend/target/performance-backend.log --output team3_fullstack/backend/target/performance-smoke/latency-new.json
```

Lượt tiếp theo dùng tên output mới vì công cụ không ghi đè. Tham số tổng quát:

```powershell
python team3_fullstack/tools/measure_latency.py --mode mock --dataset path/to/mock-questions.json --base-url http://127.0.0.1:18043 --users 1 --warmup 1 --timing-log path/to/backend.log --output path/to/new-latency.json
```

Expected: đếm đủ mẫu, tách warm-up/lỗi,4 pha ghép trace, mode MOCK_ONLY. Output mới;
không chạy vào file có sẵn. Cần ít nhất20 câu answered để smoke có20 lookup.

Live chỉ sau bàn giao Dev90 đã kiểm chứng, split report và runtime thật ready:

```powershell
python team3_fullstack/tools/measure_latency.py --mode live --dataset path/to/golden_dataset_v1.dev.json --split-report path/to/golden_dataset_v1.split.json --rag-url http://localhost:8001 --base-url http://localhost:8080 --timing-log path/to/backend.log --users 1 --warmup 1 --output path/to/new-live-latency.json
```

Expected: thiếu precondition exit2; request/timing/ngưỡng không đạt exit1. Không dùng
Golden50 thay Dev90 hoặc notebook retrieval/rerank thay pipeline LLM. Report article API
không là render Viewer; kiểm UI toàn tuần vẫn theo nhiệm vụ riêng.

Từ backend với JDK25, PostgreSQL test riêng sẵn sàng:

```powershell
.\mvnw.cmd -B -ntp "-Dtest.postgres.url=jdbc:postgresql://127.0.0.1:55442/postgres" "-Dtest.postgres.user=vlra42" package
```

Không dùng clean vì target đang chứa database/evidence local. Validate public contract
với wire do StreamApiTests vừa xuất; mọi lệnh nằm ở quickstart, biên bản chỉ ghi kết quả.

Thiết kế chức năng dùng chung: [performance-measurement.md](../../../../docs/team3_fullstack/performance-measurement.md).
