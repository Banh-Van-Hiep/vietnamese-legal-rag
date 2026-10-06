// Nhận câu trả lời dạng stream (SSE) và ghép dần vào một chuỗi.
import { useRef, useState } from "react";
import { streamQuestion } from "../api/chatApi";

export function useChatStream() {
  const [answer, setAnswer] = useState("");
  const [loading, setLoading] = useState(false);
  const abort = useRef<AbortController | null>(null);

  async function ask(question: string, conversationId?: number) {
    abort.current?.abort();
    abort.current = new AbortController();
    setAnswer("");
    setLoading(true);
    try {
      await streamQuestion(
        { question, conversationId },
        (data) => setAnswer((prev) => prev + data),
        abort.current.signal,
      );
    } finally {
      setLoading(false);
    }
  }

  return { answer, loading, ask, stop: () => abort.current?.abort() };
}
