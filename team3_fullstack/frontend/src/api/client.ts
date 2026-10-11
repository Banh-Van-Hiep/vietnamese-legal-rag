// Cấu hình base URL và xử lý lỗi. Nơi duy nhất gọi backend.
const BASE_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8080";

/** Lỗi từ backend (envelope { error: { code, message, retryable } }) hoặc lỗi kết nối. */
export class ApiError extends Error {
  constructor(
    message: string,
    public readonly status: number,
    public readonly code: string,
    public readonly retryable: boolean,
    public readonly requestId: string | null = null,
    /** Header X-Conversation-ID: có khi backend đã tiếp nhận lượt hỏi rồi mới lỗi. */
    public readonly conversationId: string | null = null,
    /** Chưa biết backend đã xử lý hay chưa (mất kết nối, quá hạn chờ). */
    public readonly outcomeUnknown = false,
  ) {
    super(message);
  }
}

interface RequestOptions {
  method?: "GET" | "POST" | "DELETE";
  json?: unknown;
  signal?: AbortSignal;
  /** Thời gian chờ tối đa của FE theo đặc tả: query 60s, document 15s. */
  timeoutMs?: number;
}

export async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const { method = "GET", json, signal, timeoutMs = 15_000 } = options;
  const controller = new AbortController();
  let timedOut = false;
  const timer = setTimeout(() => {
    timedOut = true;
    controller.abort();
  }, timeoutMs);
  const forwardAbort = () => controller.abort();
  signal?.addEventListener("abort", forwardAbort);

  try {
    let res: Response;
    try {
      res = await fetch(`${BASE_URL}${path}`, {
        method,
        headers: json === undefined
          ? { Accept: "application/json" }
          : { Accept: "application/json", "Content-Type": "application/json" },
        body: json === undefined ? undefined : JSON.stringify(json),
        signal: controller.signal,
      });
    } catch (error) {
      if (signal?.aborted) throw error; // người gọi chủ động hủy
      if (timedOut) {
        throw new ApiError("Máy chủ chưa phản hồi kịp. Hãy thử lại.", 0, "CLIENT_TIMEOUT", true, null, null, true);
      }
      throw new ApiError(
        "Không kết nối được máy chủ. Kiểm tra backend đang chạy và thử lại.",
        0, "NETWORK_ERROR", true, null, null, true,
      );
    }

    const requestId = res.headers.get("X-Request-ID");
    if (!res.ok) {
      const body = await res.json().catch(() => null);
      const detail = body?.error;
      throw new ApiError(
        detail?.message ?? `Yêu cầu thất bại (HTTP ${res.status}).`,
        res.status,
        detail?.code ?? "UNKNOWN_ERROR",
        detail?.retryable ?? false,
        requestId,
        res.headers.get("X-Conversation-ID"),
      );
    }
    if (res.status === 204) return undefined as T;
    try {
      return (await res.json()) as T;
    } catch (error) {
      if (signal?.aborted) throw error; // người gọi chủ động hủy
      // Server đã trả 2xx nhưng FE không đọc được phản hồi (đứt kết nối, quá hạn chờ, body không phải JSON).
      // Lượt hỏi có thể đã được lưu, nên đây là "chưa rõ kết quả": gửi lại phải dùng đúng client_request_id.
      throw new ApiError(
        timedOut
          ? "Máy chủ chưa phản hồi kịp. Hãy thử lại."
          : error instanceof SyntaxError
            ? "Máy chủ trả về dữ liệu không đọc được. Hãy thử lại."
            : "Mất kết nối khi nhận câu trả lời. Hãy thử lại.",
        res.status,
        timedOut ? "CLIENT_TIMEOUT" : error instanceof SyntaxError ? "INVALID_RESPONSE_BODY" : "NETWORK_ERROR",
        true,
        requestId,
        res.headers.get("X-Conversation-ID"),
        true,
      );
    }
  } finally {
    clearTimeout(timer);
    signal?.removeEventListener("abort", forwardAbort);
  }
}

export { BASE_URL };
