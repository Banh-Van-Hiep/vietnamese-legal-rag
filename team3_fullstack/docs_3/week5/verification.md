# Biên bản kiểm chứng nhiệm vụ Team 3 — Tuần 5

**Ngày kiểm tra:** 28/10/2026 (Asia/Saigon).
**Căn cứ hiện hành:** [ARCHITECTURE.md](../../../docs/ARCHITECTURE.md) (đặc tả chính),
[CODING_CONVENTIONS.md](../../../docs/CODING_CONVENTIONS.md) (quy chuẩn/DoD),
[tasks.md](tasks.md) (phân rã nhiệm vụ tuần). Jira phục vụ theo dõi công việc.
**Source kiểm tra:** `62c3556bab16e106e2e6ff29b0280a96fb738146` cùng thay đổi tài liệu chưa commit; không sửa code nghiệp vụ/test hoặc dataset để làm kết quả đạt.
**Môi trường:** Windows, JDK25/Spring Boot4.1.1, Maven Wrapper3.9.16, Node24.21,
Python3.12 trong venv kiểm thử riêng, PostgreSQL18 database riêng, Edge headless profile riêng.
**Phạm vi kết luận:** kiểm chứng kỹ thuật; chưa thay phê duyệt nhóm/gate hoặc trạng thái Jira.

**Đối chiếu nguồn ngày 28/10:** ARCHITECTURE §3/§8.2.A cho mock/API và dataset Phase1; CODING_CONVENTIONS §5/§7 cho mock protocol và DoD. Cơ cấu P0 10/8/8/4/10 là DoD cụ thể của tasks tuần5 nên vẫn phải đối chiếu, dù ticket cũ không ghi chi tiết.
Kết luận dựa trên baseline/quy chuẩn/task hiện hành, không loại tiêu chí chỉ vì Jira cũ
chưa ghi. Lượt cập nhật nguồn này không chạy lại build/test hoặc thay số liệu đã đo.

## 1. Kết luận

**G2 mock integration chạy đạt; chưa nghiệm thu trọn tuần5 do VLRA24 chưa đúng cơ cấu dataset.**
Đây là React → Java profile `rag` → PostgreSQL → HTTP mock FastAPI do Team2 cung cấp.
Không phải RAG live; profile Java `mock` cũ là API JSON khác, không dùng để suy đã đạt SSE.

## 2. Đối chiếu từng task

| Task | Expected / DoD | Actual và căn cứ | Kết luận |
| --- | --- | --- | --- |
| VLRA22 | SSE đúng protocol, no-store/timeout, REST hội thoại và disconnect an toàn | 12 `StreamApiTests` và E2E 10 chạy đạt: meta→terminal, heartbeat, insufficient không delta/citation, logical error replay, disconnect không tạo lượt AI mới. App chạy với PostgreSQL và HTTP mock không cần retrieval/LLM key. | Đạt luồng mock kiểm thử |
| VLRA23 | Chat/sidebar/SSE parser; bấm citation mở đúng Viewer | FE 72/72 + build; E2E E02–E07 đạt; Viewer kiểm thêm360px/768px không tràn ngang, có nguồn HTTPS/rel an toàn. Parser nằm ở `api/{sse,chatStream}.ts`, lifecycle ở `hooks/useChat.ts`, tương đương trách nhiệm hook trong task. | Đạt kỹ thuật mock |
| VLRA24 | File Phase1 30–50 câu, validation và cơ cấu P0 10/8/8/4/10 thiếu dữ kiện | File Team2 có40 mẫu và validator đạt, **40 answered/0 insufficient_context**. Không thỏa10 mẫu thiếu dữ kiện; category chi tiết hiện tại không phải bảng phân tầng P0 được yêu cầu. Team3 có13 mẫu riêng (12 answered/1 insufficient), chưa là bộ hợp nhất được chốt. | Chưa đạt cơ cấu/bàn giao |
| VLRA-T3-06 | CORS/trace headers và integration test mock đạt | Maven125/125, runner cấu hình37/37; `StreamApiTests` kiểm origin được phép/ngoài allowlist, headers, lỗi. E2E thực tế FE15173 gọi BE18043 thành công từ origin đã cấu hình. | Đạt kỹ thuật local |

### Kết quả dataset mới chạy

- `team2_rag/validate_golden.py`: exit0, **40/40**. File có40 mẫu đã đủ điều kiện số lượng
  30–50, nhưng validator không kiểm đủ cơ cấu P0 hoặc xác nhận pháp lý.
- `ground_truth/validate_ground_truth.py`: exit0, **13/13**. Đối chiếu corpus thật trong repo.
- Nếu chỉ đếm hợp của hai file: **53 ID/câu hỏi khác nhau**, 52 answered/1 insufficient.
  Đây không phải release dataset chung; không tự gộp hoặc đổi nhãn/đáp án để đạt chỉ tiêu.

## 3. Lệnh chạy lại

Từ frontend: `npm test`, `npm run build`. Từ repository root:

```powershell
$env:JAVA_HOME='D:/Java/jdk-25' # thay bằng JDK25 đã cài trên máy
# Tại team3_fullstack/backend, dùng PostgreSQL test riêng đã tạo:
.\mvnw.cmd -B -ntp '-Dtest.postgres.url=jdbc:postgresql://127.0.0.1:55442/postgres' '-Dtest.postgres.user=vlra42' package
# Từ root, harness cấu hình (Maven stub, không thay smoke Spring thật):
powershell -NoProfile -ExecutionPolicy Bypass -File team3_fullstack/backend/src/test/powershell/RunLocalConfigurationTests.ps1 -JavaHome 'D:/Java/jdk-25'
python -X utf8 team2_rag/validate_golden.py
python -X utf8 team3_fullstack/ground_truth/validate_ground_truth.py
```

Các giá trị port/user ở trên là test cluster riêng, không phải credential/database dùng chung.
Cần Python extras `.[api,test,rag]` trong venv và dependencies frontend theo lockfile.
Runner G2 có sẵn (trỏ PostgreSQL test đã tạo; không dùng `-CreateDb` cho port tùy chỉnh):

```powershell
powershell -ExecutionPolicy Bypass -File team3_fullstack/run-vlra44-e2e.ps1 -SkipInstall -JavaHome 'D:/Java/jdk-25' -Python '<venv>/Scripts/python.exe' -DbUrl 'jdbc:postgresql://127.0.0.1:55442/legal_rag_audit_20261028' -DbUser vlra42
```

Trong lượt này chạy JAR đã package, Vite, Edge ẩn bằng process riêng, rồi gọi trực tiếp
`frontend/tests/browser/vlra44-e2e.mjs` với FE15173/BE18043/RAG18044/CDP19242 và venv riêng.
Kịch bản tự bật/tắt FastAPI mock. E01–E10 **10/10 PASS**,0 uncaught JS exception.

## 4. Evidence và giới hạn

Dưới `backend/target/week-acceptance-20261028/` (ignored):
`backend-package.log`, `frontend-unit.json`, `frontend-build.log`, `config-runner.log`,
`golden-team2.log`, `golden-team3.log`, `inventory.json`, `e2e/{results.json,browser.png,rag-mock.log}`.
Kết quả raw là local; báo cáo ghi expected/actual để bàn giao, không coi thiếu raw log trên máy
khác là một lần kiểm thử mới. Không sửa source/runtime/dataset trong lượt này.

## 5. Điều kiện còn thiếu

Chủ trì thống nhất cơ cấu P0 và10 câu thiếu dữ kiện với người soạn/reviewer; chốt release
Phase1 nhận đóng góp của các team. Xác nhận review pháp lý và phân công, không tự sửa dữ liệu.
G2 đã kiểm chứng kỹ thuật; phê duyệt nhóm/Jira vẫn do nhóm quyết định.

**Dọn môi trường:** đã dừng các process/cluster kiểm thử do lượt này mở; xác minh các
cổng15173/18043/18044/18049/19242/55442 đã đóng. Không đụng dịch vụ PostgreSQL khác.
