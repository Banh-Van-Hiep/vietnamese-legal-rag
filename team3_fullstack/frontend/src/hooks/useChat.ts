// v2.0 turn lifecycle: backend owns IDs/state/history; UI never starts a second AI turn on uncertain retry.
import { useCallback, useEffect, useRef, useState } from "react";
import { ApiError } from "../api/client";
import { canRetry, shouldReuseRequestId } from "../api/retryPolicy";
import { sendQuery } from "../api/chatApi";
import { getAllMessages } from "../api/conversationApi";
import { numericId } from "../api/publicApi";
import { forgetTurn, pendingFor, rememberTurn, type PendingTurn } from "../api/pendingTurn";
import type { Message, UiMessage } from "../types";
import { codePointLength } from "../utils/text";
import { uuidv4 } from "../utils/uuid";

export const MAX_QUESTION_LENGTH = 2000;
const ERROR_TEXT: Record<string,string> = {
  SERVICE_UNAVAILABLE: "Dịch vụ tạm thời không sẵn sàng. Hãy thử lại sau.",
  UPSTREAM_TIMEOUT: "Dịch vụ chưa phản hồi kịp.",
  UPSTREAM_INVALID_RESPONSE: "Kết quả từ dịch vụ không hợp lệ nên không được hiển thị.",
  PERSISTENCE_UNAVAILABLE: "Chưa xác định được kết quả lưu. Hãy kiểm tra lại lượt hỏi.",
  PROCESSING_INTERRUPTED: "Lượt xử lý bị gián đoạn. Có thể gửi một lượt mới.",
  INTERNAL_ERROR: "Hệ thống gặp lỗi khi xử lý yêu cầu.",
};
const RETRYABLE = new Set(["SERVICE_UNAVAILABLE","UPSTREAM_TIMEOUT","PERSISTENCE_UNAVAILABLE","PROCESSING_INTERRUPTED"]);
function fromServer(m: Message): UiMessage {
  const result: UiMessage = { key: m.message_id, clientRequestId: m.client_request_id, role: m.role,
    state: m.state, content: m.content, answerStatus: m.answer_status, citations: m.citations };
  if (m.state === "failed") {
    const code = m.error_code ?? "INTERNAL_ERROR";
    result.failure = { code, message: ERROR_TEXT[code] ?? ERROR_TEXT.INTERNAL_ERROR, retryable: RETRYABLE.has(code), requestId: null };
  }
  return result;
}
function uncertain(draft: PendingTurn): UiMessage[] {
  return [
    { key: `u-${draft.requestId}`, clientRequestId: draft.requestId, role: "user", state: "completed", content: draft.question, answerStatus: null, citations: [] },
    { key: `a-${draft.requestId}`, clientRequestId: draft.requestId, role: "assistant", state: "failed", content: null, answerStatus: null, citations: [],
      failure: { code: "OUTCOME_UNKNOWN", message: "Chưa rõ kết quả lượt trước. Thử lại sẽ kiểm tra đúng lượt hỏi đó.", requestId: null, retryable: true, outcomeUnknown: true } },
  ];
}
interface RetryInfo { requestId: string; sameId: boolean }
export interface LoadError { message: string; notFound: boolean }
interface Options { conversationId?: string; onConversationCreated: (id: string) => void; onChanged: () => void }

export function useChat({ conversationId, onConversationCreated, onChanged }: Options) {
  const [messages, setMessages] = useState<UiMessage[]>([]);
  const [loading, setLoading] = useState(false);
  const [loadError, setLoadError] = useState<LoadError | null>(null);
  const [receiving, setReceiving] = useState(false);
  const [reloadToken, setReloadToken] = useState(0);
  const running = useRef(false), epoch = useRef(0);
  const activeId = useRef(conversationId), justCreated = useRef<string>();
  const route = useRef(conversationId); route.current = conversationId;
  const stream = useRef<AbortController>();
  const messagesRef = useRef(messages); messagesRef.current = messages;
  const retryInfo = useRef(new Map<string, RetryInfo>());
  const callbacks = useRef({ onConversationCreated, onChanged }); callbacks.current = { onConversationCreated, onChanged };

  useEffect(() => () => { epoch.current++; stream.current?.abort(); }, []);
  useEffect(() => {
    if (conversationId && justCreated.current === conversationId) { justCreated.current = undefined; return; }
    justCreated.current = undefined;
    epoch.current++; stream.current?.abort(); running.current = false; setReceiving(false);
    activeId.current = conversationId; setLoadError(null); setMessages([]);
    const myEpoch = epoch.current, controller = new AbortController();
    const draft = pendingFor(conversationId);
    if (!conversationId) {
      setLoading(false);
      if (draft) {
        retryInfo.current.set(`a-${draft.requestId}`, { requestId: draft.requestId, sameId: true });
        setMessages(uncertain(draft));
      }
      return;
    }
    setLoading(true);
    getAllMessages(conversationId, controller.signal).then((items) => {
      if (controller.signal.aborted || epoch.current !== myEpoch || route.current !== conversationId) return;
      const rows = items.map(fromServer);
      if (draft) {
        const saved = items.find((m) => m.client_request_id === draft.requestId && m.role === "assistant");
        if (saved && saved.state !== "pending") forgetTurn(draft.requestId);
        if (!saved) {
          rows.push(...uncertain(draft));
          retryInfo.current.set(`a-${draft.requestId}`, { requestId: draft.requestId, sameId: true });
        }
      }
      setMessages(rows); setLoading(false);
    }).catch((error) => {
      if (controller.signal.aborted || epoch.current !== myEpoch) return;
      setLoading(false); setLoadError({ message: error instanceof ApiError ? error.message : "Không tải được hội thoại.",
        notFound: error instanceof ApiError && error.code === "CONVERSATION_NOT_FOUND" });
    });
    return () => controller.abort();
  }, [conversationId, reloadToken]);

  const patch = useCallback((key: string, change: (m: UiMessage) => UiMessage) => {
    setMessages((all) => all.map((m) => m.key === key ? change(m) : m));
  }, []);
  const runTurn = useCallback(async (assistantKey: string, question: string, requestId: string) => {
    const myEpoch = epoch.current, originalRoute = route.current, controller = new AbortController();
    stream.current = controller;
    let target = activeId.current;
    const current = () => myEpoch === epoch.current && (route.current === originalRoute || route.current === target);
    rememberTurn({ requestId, question, conversationId: target });
    const bind = (id: string) => {
      if (!current()) return;
      numericId(id); target = id; rememberTurn({ requestId, question, conversationId: id });
      if (activeId.current !== id) {
        activeId.current = id; justCreated.current = id; callbacks.current.onConversationCreated(id);
      }
    };
    try {
      const result = await sendQuery({ question, client_request_id: requestId, conversation_id: target }, {
        signal: controller.signal,
        onMeta: (meta) => bind(String(meta.conversationId)),
        onDelta: (text) => { if (current()) patch(assistantKey, (m) => ({ ...m, content: (m.content ?? "") + text })); },
      });
      forgetTurn(requestId); retryInfo.current.delete(assistantKey);
      if (!current()) return;
      patch(assistantKey, (m) => ({ ...m, state: "completed", content: result.answer, answerStatus: result.status, citations: result.citations, failure: undefined }));
    } catch (error) {
      if (!current()) return;
      let api = error instanceof ApiError ? error : null;
      if (controller.signal.aborted) api = new ApiError("Đã dừng nhận. Máy chủ có thể vẫn đang xử lý; thử lại để nhận kết quả của cùng lượt.", 0, "RECEIVING_STOPPED", true, null, target ?? null, true);
      if (api?.conversationId) { try { bind(api.conversationId); } catch { /* Ignore malformed binding. */ } }
      const sameId = shouldReuseRequestId(api ?? error);
      if (!sameId) forgetTurn(requestId);
      retryInfo.current.set(assistantKey, { requestId, sameId });
      if (api?.code === "REQUEST_IN_PROGRESS") {
        patch(assistantKey, (m) => ({ ...m, state: "pending", content: null, failure: undefined }));
      } else if (api?.code === "CONVERSATION_BUSY") {
        setReloadToken((n) => n + 1);
      } else {
        patch(assistantKey, (m) => ({ ...m, state: "failed", content: null, citations: [], answerStatus: null,
          failure: { message: api?.message ?? "Chưa rõ kết quả. Hãy kiểm tra lại lượt hỏi.", code: api?.code ?? "UNKNOWN_ERROR",
            requestId: api?.requestId ?? null, retryable: canRetry(api ?? error), outcomeUnknown: sameId } }));
      }
    } finally {
      if (current()) { running.current = false; setReceiving(false); stream.current = undefined; }
      callbacks.current.onChanged();
    }
  }, [patch]);

  const send = useCallback((raw: string): boolean => {
    const question = raw.trim();
    if (running.current || messagesRef.current.some((m) => m.state === "pending" || m.failure?.outcomeUnknown)
      || !question || codePointLength(question) > MAX_QUESTION_LENGTH) return false;
    running.current = true; setReceiving(true);
    const requestId = uuidv4(), assistantKey = `a-${requestId}`;
    setMessages((all) => [...all,
      { key: `u-${requestId}`, clientRequestId: requestId, role: "user", state: "completed", content: question, answerStatus: null, citations: [] },
      { key: assistantKey, clientRequestId: requestId, role: "assistant", state: "pending", content: null, answerStatus: null, citations: [] },
    ]);
    void runTurn(assistantKey, question, requestId); return true;
  }, [runTurn]);
  const retry = useCallback((key: string): boolean => {
    if (running.current || messagesRef.current.some((m) => m.state === "pending")) return false;
    const list = messagesRef.current, index = list.findIndex((m) => m.key === key);
    const question = index > 0 ? list[index-1].content : null;
    if (!question) return false;
    running.current = true; setReceiving(true);
    const info = retryInfo.current.get(key);
    if (info?.sameId) {
      patch(key, (m) => ({ ...m, state: "pending", content: null, citations: [], answerStatus: null, failure: undefined }));
      void runTurn(key, question, info.requestId);
    } else {
      const requestId = uuidv4(), newKey = `a-${requestId}`;
      setMessages((all) => [...all,
        { key: `u-${requestId}`, clientRequestId: requestId, role: "user", state: "completed", content: question, answerStatus: null, citations: [] },
        { key: newKey, clientRequestId: requestId, role: "assistant", state: "pending", content: null, answerStatus: null, citations: [] },
      ]);
      void runTurn(newKey, question, requestId);
    }
    return true;
  }, [patch, runTurn]);
  const blocked = receiving || messages.some((m) => m.state === "pending" || m.failure?.outcomeUnknown);
  return { messages, loading, loadError, sending: blocked, receiving, send, retry,
    reload: useCallback(() => setReloadToken((n) => n + 1), []),
    stopReceiving: useCallback(() => stream.current?.abort(), []),
  };
}
