# Plan — kiểm chứng tuần6

1. Fetch develop và so phần code liên quan; lưu hash/source, không merge worktree.
2. Đọc HttpAiClient, StreamService/DTO, ChatStore/history và tests/FE hiện có.
3. Khởi động đúng cluster PostgreSQL test riêng đã có; chạy Maven Wrapper package
   với5 suite liên quan. Chạy FE unit/build, browser E2E FastAPI mock thực.
4. Chạy factory FastAPI thật trên loopback riêng, kiểm health/ready/query/OpenAPI và
   article lookup. Đọc cấu hình ở mức có/không/existence, không in giá trị nhạy cảm.
   Không inject pipeline giả hoặc sửa cấu hình shared để tạo PASS; không tải model.
5. Dừng đúng dịch vụ/cluster do audit mở, kiểm cổng. Ghi validation/verification và
   sửa tham chiếu cũ. Không lặp lại build/test sau PASS nếu source không đổi.

Không sửa app/test. Các suite dùng lại: HttpAiClientTests, AiResponseValidatorTests,
ChatStoreTests, PostgresChatStoreTests, StreamApiTests. Dependencies đã có trong môi
trường kiểm thử riêng; không thêm dependency vào project.
