import { afterEach, describe, expect, it, vi } from "vitest";
import { streamChat } from "./chatStream";
import { SseParser } from "./sse";
import { parseMeta } from "./publicContract";

const input = { question: "Câu hỏi", clientRequestId: "44444444-4444-4444-8444-444444444444" };
const meta = { conversationId: 101, clientRequestId: input.clientRequestId, userMessageId: 201, assistantMessageId: 202, createdAt: "2026-10-23T00:00:00Z" };
const citation = { citationId: "C1", chunkId: "mock_v1_art1_k1", documentId: "mock_v1", articleId: "art1", documentTitle: "Văn bản thử", article: "Điều 1", clause: null, point: null, sourceUrl: "https://example.com/mock" };
const complete = { ...meta, status: "answered", answer: "Đáp án kiểm thử tiếng Việt 😀 [C1].", citations: [citation] };
const frame = (event: string, data: unknown) => `event: ${event}\ndata: ${JSON.stringify(data)}\n\n`;
function response(body: string, chunkSize = 65536, headers: Record<string, string> = {}) {
  const bytes = new TextEncoder().encode(body);
  return new Response(new ReadableStream<Uint8Array>({ start(c) {
    for (let i = 0; i < bytes.length; i += chunkSize) c.enqueue(bytes.slice(i, i + chunkSize)); c.close();
  } }), { headers: { "Content-Type": "text/event-stream; charset=utf-8", "X-Request-ID": "trace-1", "X-Conversation-ID": "101", ...headers } });
}
function mock(body: string, size?: number) { vi.stubGlobal("fetch", vi.fn(async () => response(body, size))); }
const good = () => frame("meta", meta) + ": heartbeat\n\n" + frame("delta", { text: "Đáp án" }) + frame("complete", complete);
afterEach(() => { vi.unstubAllGlobals(); vi.useRealTimers(); });

describe("v2.0 SSE transport", () => {
  it.each([1, 2, 7, 2048])("decodes UTF8 across %i-byte chunks, ignores heartbeat and uses canonical complete", async (size) => {
    mock(good().replace(/\n/g, "\r\n"), size); const onMeta = vi.fn(), onDelta = vi.fn();
    await expect(streamChat(input, { onMeta, onDelta })).resolves.toEqual(complete);
    expect(onMeta).toHaveBeenCalledTimes(1); expect(onMeta).toHaveBeenCalledWith(meta);
    expect(onDelta).toHaveBeenCalledTimes(1); expect(onDelta).toHaveBeenCalledWith("Đáp án");
    const [, options] = vi.mocked(fetch).mock.calls[0];
    expect(options?.headers).toMatchObject({ Accept: "text/event-stream", "Content-Type": "application/json" });
    expect(JSON.parse(options?.body as string)).toEqual(input);
    expect(vi.mocked(fetch).mock.calls[0][0]).toMatch(/\/api\/v1\/chat\/stream$/);
  });
  it("supports multiline data, LF and fragmented frames", () => {
    const emit = vi.fn(); const p = new SseParser(emit);
    p.push("event: delta\nda"); p.push('ta: {\ndata: "text": "Tiếng Việt"}\n'); p.push("\n");
    expect(emit).toHaveBeenCalledTimes(1); expect(emit).toHaveBeenCalledWith("delta", { text: "Tiếng Việt" });
  });
  it("insufficient_context completes without invented citations or delta", async () => {
    const result = { ...meta, status: "insufficient_context", answer: "Chưa đủ căn cứ", citations: [] };
    mock(frame("meta", meta) + frame("complete", result)); const onDelta = vi.fn();
    await expect(streamChat(input, { onDelta })).resolves.toEqual(result); expect(onDelta).not.toHaveBeenCalled();
  });
  it("rejects unsafe/coerced numeric IDs", () => {
    for (const id of ["101", 0, -1, 1.5, Number.MAX_SAFE_INTEGER + 1]) expect(() => parseMeta({ ...meta, conversationId: id })).toThrow();
  });
  it.each([
    () => frame("complete", complete),
    () => frame("meta", meta) + frame("meta", meta),
    () => frame("meta", meta) + frame("unknown", {}),
    () => frame("meta", meta) + frame("complete", { ...complete, conversationId: 999 }),
    () => frame("meta", meta) + frame("complete", { ...complete, answer: "Sai nhãn [C2]" }),
    () => frame("meta", meta) + frame("complete", { ...complete, citations: [{ ...citation, point: 5 }] }),
    () => frame("meta", meta) + frame("complete", { ...complete, snippet: "extra" }),
    () => frame("meta", meta) + frame("complete", complete) + frame("complete", complete),
    () => frame("meta", meta),
    () => frame("meta", { ...meta, clientRequestId: "55555555-5555-4555-8555-555555555555" }),
  ])("rejects malformed/order/binding/terminal/semantic response as unknown outcome", async (make) => {
    mock(make()); await expect(streamChat(input)).rejects.toMatchObject({ code: "STREAM_INTERRUPTED", outcomeUnknown: true });
  });
  it("rejects a wrong response content type", async () => {
    vi.stubGlobal("fetch", vi.fn(async () => response(good(), 2048, { "Content-Type": "application/json" })));
    await expect(streamChat(input)).rejects.toMatchObject({ outcomeUnknown: true });
  });
  it("terminal SSE error is known failure with trace and bound conversation", async () => {
    mock(frame("meta", meta) + frame("error", { error: { code: "SERVICE_UNAVAILABLE", message: "Dịch vụ chưa sẵn sàng", retryable: true } }));
    await expect(streamChat(input)).rejects.toMatchObject({ code: "SERVICE_UNAVAILABLE", outcomeUnknown: false, requestId: "trace-1", conversationId: "101" });
  });
  it("persistence failure remains uncertain even with an error terminal", async () => {
    mock(frame("meta", meta) + frame("error", { error: { code: "PERSISTENCE_UNAVAILABLE", message: "Không thể ghi", retryable: true } }));
    await expect(streamChat(input)).rejects.toMatchObject({ outcomeUnknown: true });
  });
  it("logical HTTP replay error is parsed before opening stream", async () => {
    vi.stubGlobal("fetch", vi.fn(async () => new Response(JSON.stringify({ error: { code: "UPSTREAM_TIMEOUT", message: "Quá hạn", retryable: true } }), { status: 504, headers: { "Content-Type": "application/json", "X-Conversation-ID": "101" } })));
    await expect(streamChat(input)).rejects.toMatchObject({ status: 504, code: "UPSTREAM_TIMEOUT", outcomeUnknown: false });
  });
  it("a body that never delivers a terminal times out without relying on fetch to reject", async () => {
    vi.useFakeTimers();
    vi.stubGlobal("fetch", vi.fn(async () => new Response(new ReadableStream({ start(c) { c.enqueue(new TextEncoder().encode(frame("meta", meta))); } }), { headers: { "Content-Type": "text/event-stream" } })));
    const pending = expect(streamChat(input, { timeoutMs: 60000 })).rejects.toMatchObject({ code: "CLIENT_TIMEOUT", outcomeUnknown: true, conversationId: "101" });
    await vi.advanceTimersByTimeAsync(60000); await pending;
  });
  it("stop receiving aborts reads, not an AI cancellation request", async () => {
    const controller = new AbortController();
    vi.stubGlobal("fetch", vi.fn(async () => new Response(new ReadableStream({ start(c) { c.enqueue(new TextEncoder().encode(frame("meta", meta))); } }), { headers: { "Content-Type": "text/event-stream" } })));
    const result = streamChat(input, { signal: controller.signal, onMeta: () => controller.abort() });
    await expect(result).rejects.toMatchObject({ name: "AbortError" }); expect(fetch).toHaveBeenCalledTimes(1);
  });
  it("already aborted signal does not start a request", async () => {
    const controller = new AbortController(); controller.abort(); const fn = vi.fn(); vi.stubGlobal("fetch", fn);
    await expect(streamChat(input, { signal: controller.signal })).rejects.toMatchObject({ name: "AbortError" });
    expect(fn).not.toHaveBeenCalled();
  });
});
