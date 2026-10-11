// Trạng thái một cuộc hội thoại: tải lịch sử, gửi câu hỏi, thử lại. Theo luồng ở docs/team3_fullstack/team3.md mục 2.
import { useCallback, useEffect, useRef, useState } from "react";
import { ApiError } from "../api/client";
import { sendQuery } from "../api/chatApi";
import { createConversation, getAllMessages } from "../api/conversationApi";
import type { Message, UiMessage } from "../types";
import { codePointLength, truncate } from "../utils/text";
import { uuidv4 } from "../utils/uuid";

export const MAX_QUESTION_LENGTH = 2000;
const TITLE_MAX_LENGTH = 100;

/** Lượt hỏi lỗi được lưu trên server nên trong lịch sử chỉ còn mã lỗi; đây là câu hiển thị tương ứng. */
const ERROR_TEXT: Record<string, string> = {
  SERVICE_UNAVAILABLE: "Dịch vụ tạm thời không sẵn sàng. Hãy thử lại sau ít phút.",
  UPSTREAM_TIMEOUT: "Dịch vụ chưa phản hồi kịp. Hãy thử lại.",
  UPSTREAM_INVALID_RESPONSE: "Hệ thống nhận được kết quả không hợp lệ nên không hiển thị câu trả lời này.",
  PERSISTENCE_UNAVAILABLE: "Hệ thống chưa lưu được kết quả. Hãy thử lại sau.",
  PROCESSING_INTERRUPTED: "Việc xử lý bị gián đoạn. Hãy hỏi lại.",
  INTERNAL_ERROR: "Hệ thống gặp lỗi khi xử lý yêu cầu.",
};
const RETRYABLE_CODES = new Set([
  "SERVICE_UNAVAILABLE", "UPSTREAM_TIMEOUT", "PERSISTENCE_UNAVAILABLE", "PROCESSING_INTERRUPTED",
]);

function fromServer(m: Message): UiMessage {
  const base: UiMessage = {
    key: m.message_id,
    role: m.role,
    state: m.state,
    content: m.content,
    answerStatus: m.answer_status,
    citations: m.citations,
  };
  if (m.role === "assistant" && m.state === "failed") {
    const code = m.error_code ?? "INTERNAL_ERROR";
    base.failure = {
      message: ERROR_TEXT[code] ?? ERROR_TEXT.INTERNAL_ERROR,
      code,
      requestId: null,
      retryable: RETRYABLE_CODES.has(code),
    };
  }
  return base;
}

interface RetryInfo {
  requestId: string;
  /** Chưa rõ backend đã xử lý chưa: gửi lại đúng client_request_id để backend chống trùng. */
  sameId: boolean;
}

export interface LoadError {
  message: string;
  notFound: boolean;
}

interface Options {
  conversationId?: string;
  onConversationCreated: (id: string) => void;
  onChanged: () => void;
}

export function useChat({ conversationId, onConversationCreated, onChanged }: Options) {
  const [messages, setMessages] = useState<UiMessage[]>([]);
  const [loading, setLoading] = useState(false);
  const [loadError, setLoadError] = useState<LoadError | null>(null);
  const [sending, setSending] = useState(false);
  const [reloadToken, setReloadToken] = useState(0);

  const sendingRef = useRef(false);
  const activeId = useRef<string | undefined>(conversationId);
  const justCreated = useRef<string | null>(null);
  /** Tăng mỗi khi người dùng chuyển hội thoại, để bỏ qua kết quả của lượt gửi cũ. */
  const epoch = useRef(0);
  const retryInfo = useRef(new Map<string, RetryInfo>());
  const messagesRef = useRef(messages);
  messagesRef.current = messages;
  const callbacks = useRef({ onConversationCreated, onChanged });
  callbacks.current = { onConversationCreated, onChanged };

  useEffect(() => {
    activeId.current = conversationId;
    if (conversationId && justCreated.current === conversationId) {
      // Hội thoại vừa tạo từ lượt hỏi đầu: giữ nguyên tin đang hiển thị, không tải lại.
      justCreated.current = null;
      return;
    }
    epoch.current++;
    sendingRef.current = false;
    setSending(false);
    setMessages([]);
    setLoadError(null);
    if (!conversationId) {
      setLoading(false);
      return;
    }
    const controller = new AbortController();
    setLoading(true);
    getAllMessages(conversationId, controller.signal)
      .then((items) => {
        setMessages(items.map(fromServer));
        setLoading(false);
      })
      .catch((error) => {
        if (controller.signal.aborted) return;
        setLoading(false);
        setLoadError({
          message: error instanceof ApiError ? error.message : "Không tải được hội thoại.",
          notFound: error instanceof ApiError && error.code === "CONVERSATION_NOT_FOUND",
        });
      });
    return () => controller.abort();
  }, [conversationId, reloadToken]);

  const patch = useCallback((key: string, change: (m: UiMessage) => UiMessage) => {
    setMessages((list) => list.map((m) => (m.key === key ? change(m) : m)));
  }, []);

  const runTurn = useCallback(async (assistantKey: string, question: string, requestId: string) => {
    const myEpoch = epoch.current;
    try {
      let target = activeId.current;
      if (!target) {
        // Hội thoại mới: đặt tên theo câu hỏi đầu để thanh bên không toàn "Hội thoại mới".
        const created = await createConversation(truncate(question, TITLE_MAX_LENGTH));
        if (myEpoch !== epoch.current) return;
        target = created.conversation_id;
        activeId.current = target;
        justCreated.current = target;
        callbacks.current.onConversationCreated(target);
      }
      const response = await sendQuery({
        conversation_id: target,
        client_request_id: requestId,
        question,
      });
      if (myEpoch !== epoch.current) return;
      patch(assistantKey, (m) => ({
        ...m,
        state: "completed",
        content: response.answer,
        answerStatus: response.status,
        citations: response.citations,
        failure: undefined,
      }));
    } catch (error) {
      if (myEpoch !== epoch.current) return;
      const api = error instanceof ApiError ? error : null;
      retryInfo.current.set(assistantKey, {
        requestId,
        sameId: !!api && (api.outcomeUnknown || api.code === "REQUEST_IN_PROGRESS"),
      });
      patch(assistantKey, (m) => ({
        ...m,
        state: "failed",
        failure: {
          message: api?.message ?? "Có lỗi không mong đợi. Hãy thử lại.",
          code: api?.code ?? "UNKNOWN_ERROR",
          requestId: api?.requestId ?? null,
          retryable: !api || api.retryable || api.outcomeUnknown,
        },
      }));
    } finally {
      if (myEpoch === epoch.current) {
        sendingRef.current = false;
        setSending(false);
      }
      callbacks.current.onChanged();
    }
  }, [patch]);

  /** Trả về true nếu câu hỏi được nhận (để ô nhập biết có xóa nội dung hay không). */
  const send = useCallback((raw: string): boolean => {
    const question = raw.trim();
    if (sendingRef.current || !question || codePointLength(question) > MAX_QUESTION_LENGTH) return false;
    sendingRef.current = true;
    setSending(true);
    const requestId = uuidv4();
    const assistantKey = `a-${requestId}`;
    setMessages((list) => [
      ...list,
      { key: `u-${requestId}`, role: "user", state: "completed", content: question, answerStatus: null, citations: [] },
      { key: assistantKey, role: "assistant", state: "pending", content: null, answerStatus: null, citations: [] },
    ]);
    void runTurn(assistantKey, question, requestId);
    return true;
  }, [runTurn]);

  const retry = useCallback((assistantKey: string): boolean => {
    if (sendingRef.current) return false;
    const list = messagesRef.current;
    const index = list.findIndex((m) => m.key === assistantKey);
    const question = index > 0 ? list[index - 1].content : null;
    if (!question) return false;
    sendingRef.current = true;
    setSending(true);
    const info = retryInfo.current.get(assistantKey);
    if (info?.sameId) {
      // Gửi lại đúng lượt cũ: backend trả kết quả đã lưu nếu lượt đó đã xong.
      patch(assistantKey, (m) => ({ ...m, state: "pending", failure: undefined }));
      void runTurn(assistantKey, question, info.requestId);
    } else {
      // Lượt cũ đã chốt failed trên server: hỏi lại bằng ID mới, thành một lượt mới trong lịch sử.
      const requestId = uuidv4();
      const newKey = `a-${requestId}`;
      setMessages((all) => [
        ...all,
        { key: `u-${requestId}`, role: "user", state: "completed", content: question, answerStatus: null, citations: [] },
        { key: newKey, role: "assistant", state: "pending", content: null, answerStatus: null, citations: [] },
      ]);
      void runTurn(newKey, question, requestId);
    }
    return true;
  }, [patch, runTurn]);

  const reload = useCallback(() => setReloadToken((n) => n + 1), []);

  return { messages, loading, loadError, sending, send, retry, reload };
}
