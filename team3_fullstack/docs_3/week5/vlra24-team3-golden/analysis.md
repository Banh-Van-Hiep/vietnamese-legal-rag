# Analyze trước triển khai — 29/10/2026

Spec/plan/tasks thống nhất50 mẫu tại nguồn chung, xóa bản riêng sau PASS và rà ngữ
nghĩa riêng bên cạnh validator. Quyết định mới thay yêu cầu cũ giữ subset riêng/nguyên
mọi record. Không đổi API/schema/quota; không có xung đột chặn phạm vi này.

Rủi ro: validator không phát hiện trùng ý, cần bảng50 ý định và đối chiếu đáp án.
Rủi ro:50 mẫu/PASS format chưa đủ10 insufficient theo DoD; phải giữ nghiệm thu mở.
Tasks có bước kiểm/báo cáo tương ứng; không cần tự sửa yêu cầu nguồn.
