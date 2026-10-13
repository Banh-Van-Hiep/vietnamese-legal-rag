import { describe, expect, it } from "vitest";
import { ApiError } from "./client";
import { canRetry, shouldReuseRequestId } from "./retryPolicy";

const serverError = (status: number, code: string, retryable: boolean) =>
  new ApiError("m", status, code, retryable, "req", null, false);
const unknownOutcome = (code: string) => new ApiError("m", 0, code, true, null, null, true);

describe("shouldReuseRequestId: giữ client_request_id khi chưa chắc server đã xử lý", () => {
  it.each(["NETWORK_ERROR", "CLIENT_TIMEOUT", "INVALID_RESPONSE_BODY"])("%s -> giữ ID", (code) => {
    expect(shouldReuseRequestId(unknownOutcome(code))).toBe(true);
  });

  it("REQUEST_IN_PROGRESS -> giữ ID (lượt cũ vẫn đang xử lý)", () => {
    expect(shouldReuseRequestId(serverError(409, "REQUEST_IN_PROGRESS", true))).toBe(true);
  });

  it("lỗi không phải ApiError (không rõ nguồn) -> giữ ID cho an toàn", () => {
    expect(shouldReuseRequestId(new TypeError("terminated"))).toBe(true);
    expect(shouldReuseRequestId(new DOMException("aborted", "AbortError"))).toBe(true);
    expect(shouldReuseRequestId("lỗi lạ")).toBe(true);
  });

  it.each([
    [503, "SERVICE_UNAVAILABLE"],
    [504, "UPSTREAM_TIMEOUT"],
    [502, "UPSTREAM_INVALID_RESPONSE"],
    [409, "CONVERSATION_BUSY"],
  ])("server đã chốt lượt thất bại (%i %s) -> dùng ID mới", (status, code) => {
    expect(shouldReuseRequestId(serverError(status, code, true))).toBe(false);
  });
});

describe("canRetry", () => {
  it("cho thử lại với lỗi tạm thời, chưa rõ kết quả và lỗi lạ", () => {
    expect(canRetry(serverError(503, "SERVICE_UNAVAILABLE", true))).toBe(true);
    expect(canRetry(unknownOutcome("NETWORK_ERROR"))).toBe(true);
    expect(canRetry(new TypeError("x"))).toBe(true);
  });

  it("không cho thử lại với lỗi đầu vào hoặc không tìm thấy", () => {
    expect(canRetry(serverError(400, "INVALID_REQUEST", false))).toBe(false);
    expect(canRetry(serverError(404, "CONVERSATION_NOT_FOUND", false))).toBe(false);
  });
});
