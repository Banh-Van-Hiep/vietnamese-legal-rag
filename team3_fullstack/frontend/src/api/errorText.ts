// Lỗi của một lượt đã lưu trên server: lịch sử chỉ còn mã lỗi, nên câu hiển thị và quyền thử lại
// được suy ra từ bảng lỗi ARCHITECTURE §7 / CODING_CONVENTIONS §4.2. Lỗi nhận trực tiếp qua SSE
// dùng nguyên `message` và `retryable` do Backend gửi, không đi qua bảng này.

export const ERROR_TEXT: Readonly<Record<string, string>> = {
  SERVICE_UNAVAILABLE: "Dịch vụ tạm thời không sẵn sàng. Hãy thử lại sau.",
  UPSTREAM_TIMEOUT: "Dịch vụ chưa phản hồi kịp.",
  UPSTREAM_INVALID_RESPONSE: "Kết quả từ dịch vụ không hợp lệ nên không được hiển thị.",
  UPSTREAM_CONTRACT_ERROR: "Dịch vụ xử lý từ chối yêu cầu nội bộ.",
  UPSTREAM_ERROR: "Dịch vụ xử lý gặp lỗi.",
  PERSISTENCE_UNAVAILABLE: "Chưa xác định được kết quả lưu. Hãy kiểm tra lại lượt hỏi.",
  PROCESSING_INTERRUPTED: "Lượt xử lý bị gián đoạn. Có thể gửi một lượt mới.",
  INTERNAL_ERROR: "Hệ thống gặp lỗi khi xử lý yêu cầu.",
};

/** Mã có `retryable = true` trong bảng lỗi chung; mã khác (kể cả mã lạ) không cho thử lại. */
export const RETRYABLE_CODES: ReadonlySet<string> = new Set([
  "SERVICE_UNAVAILABLE", "UPSTREAM_TIMEOUT", "PERSISTENCE_UNAVAILABLE", "PROCESSING_INTERRUPTED",
]);

export function storedFailure(code: string | null) {
  const known = code ?? "INTERNAL_ERROR";
  return {
    code: known,
    message: ERROR_TEXT[known] ?? ERROR_TEXT.INTERNAL_ERROR,
    retryable: RETRYABLE_CODES.has(known),
    requestId: null,
  };
}
