# Research — VLRA-41

- Nguồn gốc Docs v2.0 §8/9; quyết định người dùng 23/10 áp dụng v2.0, W4-Q1 resolved.
- Fresh origin/develop 3d64c4d: no Python HTTP server, Java HTTP placeholder. Không tự thực hiện Team2.
- JDBC nằm sẵn trong dependency tree; dùng transaction SQL rõ ràng cho receipt/lock thay vì
  kích hoạt placeholder JpaRepository trỏ tới record không phải entity. Không thay framework.
- Profile rag tách legacy mock để giữ bằng chứng tuần2; không hai chat route chính đồng thời.
- SseEmitter callback lỗi transport không đánh failed kết quả đã commit.
  [Spring MVC async](https://www.springframework.org/spring/reference/7.1/web/webmvc/mvc-ann-async.html).
- H2 test không thay PostgreSQL runtime. Docker engine chưa chạy; có service PostgreSQL local,
  chưa xác minh credential/khả năng tạo schema test. Không in secret hoặc đổi DB người dùng.

- Đã kiểm chứng H2 2.4.240 lỗi CHECK(IN) qua connection khác (issue upstream #4302); test-only dependency2.5.250 sửa lỗi, không bỏ constraint. PostgreSQL18 test cluster riêng đã chạy và dừng; xem verification.
