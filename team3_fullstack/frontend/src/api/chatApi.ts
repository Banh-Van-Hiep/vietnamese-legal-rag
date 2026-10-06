// API hỏi đáp: POST /api/v1/chat/stream, nhận câu trả lời dạng SSE.
import { BASE_URL } from "./client";
import type { ChatRequest } from "../types";

/**
 * Gửi câu hỏi và gọi onData cho mỗi sự kiện SSE nhận được.
 * Định dạng nội dung của "data:" chờ thống nhất với backend/contracts.
 */
export async function streamQuestion(
  body: ChatRequest,
  onData: (data: string) => void,
  signal?: AbortSignal,
): Promise<void> {
  const res = await fetch(`${BASE_URL}/api/v1/chat/stream`, {
    method: "POST",
    headers: { "Content-Type": "application/json", Accept: "text/event-stream" },
    body: JSON.stringify(body),
    signal,
  });
  if (!res.ok || !res.body) {
    throw new Error(`Lỗi ${res.status}: ${await res.text()}`);
  }

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  for (;;) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const events = buffer.split("\n\n");
    buffer = events.pop() ?? "";
    for (const event of events) {
      const data = event
        .split("\n")
        .filter((l) => l.startsWith("data:"))
        .map((l) => l.slice(5).trimStart())
        .join("\n");
      if (data) onData(data);
    }
  }
}
