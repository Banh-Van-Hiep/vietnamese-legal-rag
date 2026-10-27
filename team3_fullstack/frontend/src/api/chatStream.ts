import { ApiError, BASE_URL } from "./client";
import { errorDetail, object, parseComplete, parseMeta, requireValue, safeId, text, uuid } from "./publicContract";
import { SseParser } from "./sse";
import type { ChatComplete, ChatMeta, ChatRequestV2 } from "../types/publicApi";

interface StreamOptions {
  signal?: AbortSignal;
  onMeta?: (meta: ChatMeta) => void;
  onDelta?: (value: string) => void;
  timeoutMs?: number;
}
function abortable<T>(promise: Promise<T>, signal: AbortSignal): Promise<T> {
  if (signal.aborted) return Promise.reject(new DOMException("Stopped receiving", "AbortError"));
  return new Promise((resolve, reject) => {
    const abort = () => reject(new DOMException("Stopped receiving", "AbortError"));
    signal.addEventListener("abort", abort, { once: true });
    promise.then(resolve, reject).finally(() => signal.removeEventListener("abort", abort));
  });
}
/** One attempt, never auto-retries. Caller owns the UUID and replay policy. */
export async function streamChat(input: ChatRequestV2, options: StreamOptions = {}): Promise<ChatComplete> {
  requireValue(text(input.question, 2000) && uuid(input.clientRequestId));
  requireValue(input.conversationId == null || safeId(input.conversationId));
  const controller = new AbortController();
  const abort = () => controller.abort();
  options.signal?.addEventListener("abort", abort);
  if (options.signal?.aborted) controller.abort();
  let timedOut = false, requestId: string | null = null, conversationId: string | null = null;
  const timer = setTimeout(() => { timedOut = true; controller.abort(); }, options.timeoutMs ?? 60000);
  let reader: ReadableStreamDefaultReader<Uint8Array> | undefined;
  let meta: ChatMeta | undefined, complete: ChatComplete | undefined, terminalError: ApiError | undefined;
  let terminal = false;
  let deltaLength = 0;
  try {
    if (controller.signal.aborted) throw new DOMException("Stopped receiving", "AbortError");
    const res = await abortable(fetch(`${BASE_URL}/api/v1/chat/stream`, {
      method: "POST", headers: { "Content-Type": "application/json", Accept: "text/event-stream" },
      body: JSON.stringify({ question: input.question.trim(), clientRequestId: input.clientRequestId,
        ...(input.conversationId == null ? {} : { conversationId: input.conversationId }) }), signal: controller.signal,
    }), controller.signal);
    requestId = res.headers.get("X-Request-ID"); conversationId = res.headers.get("X-Conversation-ID");
    if (!res.ok) {
      let detail;
      try { detail = errorDetail(await abortable(res.json(), controller.signal)); }
      catch { throw new ApiError("Không đọc được phản hồi lỗi. Hãy kiểm tra lại lượt hỏi.", res.status, "INVALID_RESPONSE_BODY", true, requestId, conversationId, true); }
      throw new ApiError(detail.message, res.status, detail.code, detail.retryable, requestId, conversationId,
        detail.code === "PERSISTENCE_UNAVAILABLE");
    }
    requireValue(res.status === 200 && res.headers.get("Content-Type")?.split(";")[0].trim().toLowerCase() === "text/event-stream" && res.body);
    const parser = new SseParser((event, data) => {
      requireValue(!terminal);
      if (event === "meta") {
        requireValue(!meta); meta = parseMeta(data);
        requireValue(meta.clientRequestId === input.clientRequestId && (input.conversationId == null || meta.conversationId === input.conversationId));
        if (conversationId !== null) requireValue(conversationId === String(meta.conversationId));
        conversationId = String(meta.conversationId); options.onMeta?.(meta); return;
      }
      requireValue(meta);
      if (event === "delta") {
        const value = object(data, ["text"]); requireValue(typeof value.text === "string" && Array.from(value.text).length <= 12000);
        deltaLength += Array.from(value.text).length; requireValue(deltaLength <= 12000);
        options.onDelta?.(value.text); return;
      }
      if (event === "complete") { complete = parseComplete(data, meta); terminal = true; return; }
      if (event === "error") {
        const e = errorDetail(data); terminalError = new ApiError(e.message, 200, e.code, e.retryable, requestId, conversationId,
          e.code === "PERSISTENCE_UNAVAILABLE"); terminal = true; return;
      }
      throw new Error("Unknown SSE event");
    });
    reader = res.body.getReader(); const decoder = new TextDecoder("utf-8", { fatal: true });
    while (!terminal) {
      const { done, value } = await abortable(reader.read(), controller.signal);
      if (done) { parser.push(decoder.decode()); break; }
      parser.push(decoder.decode(value, { stream: true }));
    }
    if (terminalError) throw terminalError;
    requireValue(complete); return complete;
  } catch (error) {
    if (options.signal?.aborted) throw new DOMException("Stopped receiving", "AbortError");
    if (timedOut) throw new ApiError("Máy chủ chưa phản hồi kịp. Hãy kiểm tra lại lượt hỏi.", 0, "CLIENT_TIMEOUT", true, requestId, conversationId, true);
    if (error instanceof ApiError) throw error;
    throw new ApiError("Kết nối bị gián đoạn hoặc dữ liệu không hợp lệ. Hãy kiểm tra lại lượt hỏi.", 0,
      "STREAM_INTERRUPTED", true, requestId, conversationId, true);
  } finally {
    clearTimeout(timer); options.signal?.removeEventListener("abort", abort);
    void reader?.cancel().catch(() => undefined);
  }
}
