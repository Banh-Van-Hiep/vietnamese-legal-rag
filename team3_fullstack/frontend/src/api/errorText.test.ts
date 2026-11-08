import { describe, expect, it } from "vitest";
import { ERROR_TEXT, RETRYABLE_CODES, storedFailure } from "./errorText";

// ARCHITECTURE §7 / CODING_CONVENTIONS §4.2: retryable của từng mã lỗi public có thể lưu vào lượt failed.
const TABLE: Array<[string, boolean]> = [
  ["SERVICE_UNAVAILABLE", true], ["UPSTREAM_TIMEOUT", true], ["PERSISTENCE_UNAVAILABLE", true],
  ["PROCESSING_INTERRUPTED", true], ["UPSTREAM_INVALID_RESPONSE", false], ["UPSTREAM_CONTRACT_ERROR", false],
  ["UPSTREAM_ERROR", false], ["INTERNAL_ERROR", false],
];

describe("lỗi của lượt đã lưu (VLRA-70)", () => {
  it.each(TABLE)("%s có câu riêng và retryable = %s theo bảng lỗi chung", (code, retryable) => {
    const failure = storedFailure(code);
    expect(failure).toEqual({ code, message: ERROR_TEXT[code], retryable, requestId: null });
    expect(failure.message).not.toMatch(/[A-Z]{3,}_[A-Z]/); // không lộ mã kỹ thuật trong câu cho người dùng
  });
  it("mã lạ hoặc thiếu mã: câu an toàn chung và không cho thử lại", () => {
    expect(storedFailure("SOMETHING_NEW")).toMatchObject({ code: "SOMETHING_NEW", message: ERROR_TEXT.INTERNAL_ERROR, retryable: false });
    expect(storedFailure(null)).toMatchObject({ code: "INTERNAL_ERROR", retryable: false });
  });
  it("chỉ các mã retryable trong bảng mới được thử lại", () => {
    expect([...RETRYABLE_CODES].sort()).toEqual(TABLE.filter(([, r]) => r).map(([c]) => c).sort());
  });
});
