// Quy tắc gửi lại một lượt hỏi (docs/team3_fullstack/team3.md mục 1.10 và 2.3).
import { ApiError } from "./client";

/**
 * Có nên gửi lại bằng đúng client_request_id cũ không.
 * Gửi lại cùng ID luôn an toàn vì backend trả kết quả đã lưu hoặc báo đang xử lý, không tạo lượt trùng.
 * Chỉ dùng ID mới khi server đã trả lời rõ ràng là lượt đó thất bại. Lỗi nào không chắc chắn thì giữ ID.
 */
export function shouldReuseRequestId(error: unknown): boolean {
  if (!(error instanceof ApiError)) return true;
  return error.outcomeUnknown || error.code === "REQUEST_IN_PROGRESS";
}

/** Có hiện nút "Thử lại" không. */
export function canRetry(error: unknown): boolean {
  if (!(error instanceof ApiError)) return true;
  return error.retryable || error.outcomeUnknown;
}
