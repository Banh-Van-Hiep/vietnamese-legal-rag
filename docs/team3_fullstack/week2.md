# Team 3 — Nhiệm vụ chung tuần 2

**Dự án:** Vietnamese Legal RAG Assistant. **Cập nhật:** 12/10/2026.

Tuần 2 có **3 nhiệm vụ Jira**: VLRA-22, VLRA-23 và VLRA-24.
Tài liệu này ghi mục tiêu, phạm vi và đầu ra của các nhiệm vụ chung.
Việc chia nhỏ, thứ tự thực hiện và kiểm chứng thuộc `specs/`.

## 1. Nhiệm vụ và đầu ra

| Jira | Nhiệm vụ | Đầu ra cần bàn giao | Phụ trách |
| --- | --- | --- | --- |
| [VLRA-22](https://banhvanhiep.atlassian.net/browse/VLRA-22) | Khởi tạo khung Backend — Spring Boot Skeleton | Project Java/Spring Boot có cấu trúc Backend, dependency cơ bản, CORS, `.env`/biến môi trường và API mock. API nhận request/trả response theo schema thống nhất; Backend chạy ổn định, sẵn sàng tích hợp Team 2 và Frontend. | Team 3 — Backend/API |
| [VLRA-23](https://banhvanhiep.atlassian.net/browse/VLRA-23) | Khởi tạo khung Frontend — Frontend Skeleton | Khung Frontend có Router, Tailwind/UI library, Chat UI và Legal Document Viewer ban đầu. Tiếp tục React/TypeScript/Vite hiện có theo lựa chọn của Team 3. | Team 3 — UI |
| [VLRA-24](https://banhvanhiep.atlassian.net/browse/VLRA-24) | Golden Dataset Phase 1 — 30–50 câu | Mỗi thành viên đóng góp 5–10 câu hỏi pháp lý thực tế, có câu trả lời chuẩn và căn cứ `chunk_id`. Tổng dataset chung đạt 30–50 câu. | Các thành viên; Team 3 bàn giao phần đóng góp của nhóm |

VLRA-22/VLRA-23 thuộc [VLRA-4](https://banhvanhiep.atlassian.net/browse/VLRA-4);
VLRA-24 thuộc [VLRA-5](https://banhvanhiep.atlassian.net/browse/VLRA-5).
Nội dung Jira được ghi theo mô tả đã cung cấp; tài liệu này không cập nhật trạng thái trên Jira.

## 2. Phạm vi và nguồn áp dụng

- Kế thừa Backend Java/Spring Boot/Maven và Frontend React/TypeScript/Vite hiện có.
- API, luồng và kiến trúc dùng [team3.md](team3.md); interface liên team phối hợp qua
  [contracts/](../../contracts/README.md). Không tự đổi API hoặc thực hiện phần của team khác.
- Backend/API và UI được kiểm chứng local với mock trong tuần 2; tích hợp RAG thật,
  PostgreSQL production, auth, streaming và deployment không thuộc đợt bàn giao này.
- Golden Dataset dùng corpus và định dạng nhóm đã chọn. Nguồn, phiên bản văn bản,
  đáp án và phần đóng góp phải được review trước nghiệm thu; mục tiêu 30–50 là của dataset chung.

## 3. Điều kiện hoàn thành nhiệm vụ Jira

| Jira | Điều kiện hoàn thành ở cấp nhiệm vụ chung |
| --- | --- |
| VLRA-22 | Khung Backend, cấu hình và API mock đáp ứng đầu ra ở mục 1; có kiểm chứng vận hành/schema và bàn giao để phối hợp tích hợp. |
| VLRA-23 | Khung Frontend, Router, styling, Chat/Viewer đáp ứng đầu ra ở mục 1; có kiểm chứng giao diện và bàn giao cách chạy. |
| VLRA-24 | Có đủ đóng góp 5–10 câu mỗi thành viên và tổng dataset 30–50 câu, đáp án/căn cứ đã được review; bộ dữ liệu được bàn giao cho đánh giá RAG. |

Chỉ kết luận nhiệm vụ Jira đạt sau khi các task triển khai liên quan được kiểm chứng và
đối chiếu lại với đầu ra ở trên. Trạng thái Jira thực tế do nhóm cập nhật theo workflow.

## 4. Theo dõi triển khai và nghiệm thu

[Bộ triển khai tuần 2 trong specs/](../../specs/team3-week2/tasks.md) chứa phân rã task;
[báo cáo nghiệm thu](../../specs/team3-week2/verification.md) ghi bằng chứng từng task
và tổng hợp ngược lên 3 nhiệm vụ Jira.

Theo lần kiểm chứng ngày 12/10/2026, Backend/Frontend đã đạt kỹ thuật local;
còn xác nhận bàn giao của thành viên khác. Golden Dataset còn review pháp lý và
mục tiêu số lượng chung. Chưa đóng toàn tuần 2 hoặc tự đánh dấu các ticket Jira hoàn thành.
