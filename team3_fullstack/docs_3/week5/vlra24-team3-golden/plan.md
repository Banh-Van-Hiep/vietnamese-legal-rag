# Plan — hợp nhất Golden Dataset

[Spec](spec.md). Bảo toàn worktree, không đổi API/schema/dependency.

1. Lưu2 bản đầu vào và hash corpus/validator trong target ignored.
2. Đọc50 câu/đáp án và chunk nguồn; rà ý định. Giữ38/40 nội dung record chung (không tính author) và6/10 đóng góp,
   sửa gold_016/021, thay4 câu bằng gold_041–044 có căn cứ.
3. Ghi50 mẫu vào file chung tại Team2; chạy validator mặc định và kiểm bổ sung.
4. So sánh record/hash, field/type/status/NFC/chunk/dedup; lưu bảng50 ý định.
5. Sau PASS mới xóa3 file đã kiểm kê trong ground_truth qua đường dẫn workspace
   đã xác minh; không xóa file khác. Cập nhật lệnh và hồ sơ Team3 tuần4/5.
6. Kiểm link/diff, ghi validation và verification. Không chạy build FE/BE vì không
   sửa app/config, commit theo yêu cầu bàn giao; không push. Không sửa tài liệu/code Team1/2 khác.

Quyết định người dùng cho phép sửa bộ dữ liệu chung; không tự mở rộng ranh giới code.
