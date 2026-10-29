# Quickstart kiểm chứng tuần6

Từ backend, JAVA_HOME trỏ JDK25, cluster PostgreSQL test riêng sẵn sàng:

```powershell
.\mvnw.cmd -B -ntp "-Dtest=HttpAiClientTests,AiResponseValidatorTests,ChatStoreTests,PostgresChatStoreTests,StreamApiTests" "-Dtest.postgres.url=jdbc:postgresql://127.0.0.1:55442/postgres" "-Dtest.postgres.user=vlra42" package
```

Từ frontend: `npm.cmd test`, `npm.cmd run build`. Browser E2E dùng harness hiện có
`tests/browser/vlra44-e2e.mjs` với PostgreSQL database test riêng và FastAPI HTTP mock.
Factory thật: `python -m uvicorn team2_rag.api:create_app --factory --host 127.0.0.1 --port 18049`.
Kiểm /internal/v1/health, /ready, POST /query và route article; không dùng mock để
đánh giá ready/live. [Validation](validation.md) ghi đúng source/lệnh/kết quả và giới hạn.
