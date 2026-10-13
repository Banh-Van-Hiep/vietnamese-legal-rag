import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { ApiError, request } from "./client";

const okHeaders = () => new Headers({ "X-Request-ID": "req-1", "X-Conversation-ID": "conv-1" });

function mockFetch(impl: () => Partial<Response> | Promise<Partial<Response>>) {
  vi.stubGlobal("fetch", vi.fn(async () => impl() as Response));
}

async function failure(): Promise<ApiError> {
  try {
    await request("/x", { method: "POST", json: {}, timeoutMs: 60_000 });
  } catch (error) {
    expect(error).toBeInstanceOf(ApiError);
    return error as ApiError;
  }
  throw new Error("request đáng lẽ phải lỗi");
}

afterEach(() => vi.unstubAllGlobals());

describe("request: lỗi sau khi server đã phản hồi 2xx (chưa rõ kết quả)", () => {
  // Đây là lỗi T04: trước đây các lỗi này thoát ra dưới dạng TypeError/DOMException/SyntaxError,
  // nên giao diện gửi lại bằng client_request_id mới và server lưu trùng lượt hỏi.
  const cases: Array<[string, Error, string]> = [
    ["đứt kết nối khi đọc body", new TypeError("terminated"), "NETWORK_ERROR"],
    ["body không phải JSON", new SyntaxError("Unexpected token <"), "INVALID_RESPONSE_BODY"],
  ];

  for (const [name, thrown, code] of cases) {
    it(`${name} -> ApiError chưa rõ kết quả, giữ header để lần sau gửi lại đúng ID`, async () => {
      mockFetch(() => ({ ok: true, status: 200, headers: okHeaders(), json: async () => { throw thrown; } }));
      const error = await failure();
      expect(error.code).toBe(code);
      expect(error.outcomeUnknown).toBe(true);
      expect(error.retryable).toBe(true);
      expect(error.requestId).toBe("req-1");
      expect(error.conversationId).toBe("conv-1");
    });
  }

  it("quá hạn chờ khi đang đọc body -> CLIENT_TIMEOUT", async () => {
    vi.useFakeTimers();
    try {
      mockFetch(() => ({
        ok: true, status: 200, headers: okHeaders(),
        // body treo vĩnh viễn: chỉ kết thúc khi FE hủy do hết hạn
        json: () => new Promise((_, reject) => setTimeout(() => reject(new DOMException("aborted", "AbortError")), 90_000)),
      }));
      const pending = failure();
      await vi.advanceTimersByTimeAsync(60_000); // đến hạn chờ của FE
      await vi.advanceTimersByTimeAsync(30_000); // body mới báo lỗi
      const error = await pending;
      expect(error.code).toBe("CLIENT_TIMEOUT");
      expect(error.outcomeUnknown).toBe(true);
    } finally {
      vi.useRealTimers();
    }
  });

  it("người gọi chủ động hủy thì không bị coi là lỗi cần thử lại", async () => {
    const controller = new AbortController();
    mockFetch(() => ({
      ok: true, status: 200, headers: okHeaders(),
      json: async () => { controller.abort(); throw new DOMException("aborted", "AbortError"); },
    }));
    await expect(request("/x", { signal: controller.signal })).rejects.toMatchObject({ name: "AbortError" });
  });
});

describe("request: các trường hợp còn lại giữ nguyên hành vi", () => {
  beforeEach(() => vi.unstubAllGlobals());

  it("2xx hợp lệ trả về JSON", async () => {
    mockFetch(() => ({ ok: true, status: 200, headers: okHeaders(), json: async () => ({ a: 1 }) }));
    await expect(request("/x")).resolves.toEqual({ a: 1 });
  });

  it("204 không đọc body", async () => {
    mockFetch(() => ({ ok: true, status: 204, headers: okHeaders(), json: async () => { throw new Error("không được đọc"); } }));
    await expect(request("/x", { method: "DELETE" })).resolves.toBeUndefined();
  });

  it("lỗi từ server: lấy code/message/retryable từ envelope, KHÔNG phải chưa rõ kết quả", async () => {
    mockFetch(() => ({
      ok: false, status: 503, headers: okHeaders(),
      json: async () => ({ error: { code: "SERVICE_UNAVAILABLE", message: "Dịch vụ tạm thời không sẵn sàng.", retryable: true } }),
    }));
    const error = await failure();
    expect(error).toMatchObject({ status: 503, code: "SERVICE_UNAVAILABLE", retryable: true, outcomeUnknown: false, requestId: "req-1" });
  });

  it("lỗi server có body hỏng vẫn thành ApiError", async () => {
    mockFetch(() => ({ ok: false, status: 502, headers: okHeaders(), json: async () => { throw new SyntaxError("x"); } }));
    const error = await failure();
    expect(error).toMatchObject({ status: 502, code: "UNKNOWN_ERROR", outcomeUnknown: false });
  });

  it("không kết nối được (fetch lỗi) -> NETWORK_ERROR chưa rõ kết quả", async () => {
    vi.stubGlobal("fetch", vi.fn(async () => { throw new TypeError("Failed to fetch"); }));
    const error = await failure();
    expect(error).toMatchObject({ code: "NETWORK_ERROR", outcomeUnknown: true });
  });
});
