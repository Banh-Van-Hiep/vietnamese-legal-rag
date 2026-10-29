# Quickstart nghiệm thu tuần7

Evidence IDEM:3 suite ChatStoreTests/PostgresChatStoreTests/StreamApiTests đã PASS
29/10 trong Maven package tuần6. Đối chiếu hash source trước khi dùng lại; không cần
chạy lại nếu không đổi code. [Validation](validation.md) ghi tên case/ma trận.

Khi cần tái lập từ backend với JDK25 và PostgreSQL test riêng:

```powershell
.\mvnw.cmd -B -ntp "-Dtest=ChatStoreTests,PostgresChatStoreTests,StreamApiTests" "-Dtest.postgres.url=jdbc:postgresql://127.0.0.1:55442/postgres" "-Dtest.postgres.user=vlra42" test
```

Viewer probe chạy trên FE15173/Java18043/Python mock18044/CDP19242 với database
legal_rag_week7_20261029; helper ignored dưới target/week7-acceptance-20261029.
Dừng các tiến trình/cluster test audit mở. Không dùng DB thật hoặc profile browser cá nhân.
Golden kiểm kê ở team2_rag/data/golden, không cộng sample5qa vào release Phase1/v1.
