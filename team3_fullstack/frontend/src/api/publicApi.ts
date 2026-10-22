/** Explicit adapter: public v2.0 wire objects -> existing presentation models. */
import { ApiError, request } from "./client";
import { checkAnswer, httpsUrl, legalId, object, parseCitation, requireValue, safeId, text, timestamp, uuid } from "./publicContract";
import type { ArticleResponse, Citation, Conversation, Message } from "../types";
import type { PublicCitation } from "../types/publicApi";

export function numericId(value: string): number {
  const id = Number(value);
  requireValue(/^[1-9][0-9]*$/.test(value) && safeId(id)); return id;
}
export function citationModel(c: PublicCitation): Citation {
  return { citation_id: c.citationId, chunk_id: c.chunkId, document_id: c.documentId, article_id: c.articleId,
    document_title: c.documentTitle, article: c.article, clause: c.clause, point: c.point, source_url: c.sourceUrl };
}
function conversation(value: unknown): Conversation {
  const c = object(value, ["id", "title", "createdAt", "updatedAt"]);
  requireValue(safeId(c.id) && text(c.title, 100) && timestamp(c.createdAt) && timestamp(c.updatedAt));
  return { conversation_id: String(c.id), title: c.title, created_at: c.createdAt, updated_at: c.updatedAt };
}
function message(value: unknown, target: number): Message {
  const m = object(value, ["id", "conversationId", "clientRequestId", "sequenceNo", "role", "state", "content", "answerStatus", "citations", "errorCode", "createdAt"]);
  requireValue(safeId(m.id) && m.conversationId === target && uuid(m.clientRequestId) && safeId(m.sequenceNo) && timestamp(m.createdAt));
  requireValue((m.role === "user" || m.role === "assistant") && ["pending", "completed", "failed"].includes(String(m.state)) && Array.isArray(m.citations));
  const citations = m.citations.map(parseCitation).map(citationModel);
  if (m.role === "user") {
    requireValue(m.state === "completed" && text(m.content, 2000) && m.answerStatus === null && m.errorCode === null && !citations.length);
  } else if (m.state === "completed") {
    checkAnswer(m.answerStatus, m.content, m.citations); requireValue(m.errorCode === null);
  } else {
    requireValue(m.content === null && m.answerStatus === null && !citations.length);
    requireValue(m.state === "failed" ? text(m.errorCode, 60) : m.errorCode === null);
  }
  return { message_id: String(m.id), conversation_id: String(target), client_request_id: m.clientRequestId,
    sequence_no: m.sequenceNo, role: m.role, state: m.state as Message["state"], content: m.content as string | null,
    answer_status: m.answerStatus as Message["answer_status"], citations, error_code: m.errorCode as string | null, created_at: m.createdAt };
}
async function adapt<T>(result: Promise<unknown>, parse: (value: unknown) => T): Promise<T> {
  try { return parse(await result); }
  catch (e) {
    if (e instanceof ApiError || e instanceof DOMException && e.name === "AbortError") throw e;
    throw new ApiError("Dữ liệu máy chủ không khớp yêu cầu. Hãy tải lại.", 502, "INVALID_RESPONSE_BODY", true);
  }
}
export function v2Conversations(signal?: AbortSignal): Promise<Conversation[]> {
  return adapt(request("/api/v1/conversations", { signal }), (value) => {
    requireValue(Array.isArray(value)); const rows = value.map(conversation);
    requireValue(new Set(rows.map((c) => c.conversation_id)).size === rows.length); return rows;
  });
}
export function v2CreateConversation(title: string, signal?: AbortSignal) {
  return adapt(request("/api/v1/conversations", { method: "POST", json: { title }, signal }), conversation);
}
export function v2DeleteConversation(id: string) {
  return request<void>(`/api/v1/conversations/${numericId(id)}`, { method: "DELETE" });
}
export function v2Messages(id: string, signal?: AbortSignal): Promise<Message[]> {
  const target = numericId(id);
  return adapt(request(`/api/v1/conversations/${target}/messages`, { signal }), (value) => {
    requireValue(Array.isArray(value)); const rows = value.map((m) => message(m, target));
    requireValue(new Set(rows.map((m) => m.message_id)).size === rows.length);
    requireValue(rows.every((m, i) => i === 0 || m.sequence_no > rows[i-1].sequence_no)); return rows;
  });
}
export function v2Article(documentId: string, articleId: string, signal?: AbortSignal): Promise<ArticleResponse> {
  requireValue(legalId(documentId, 200) && legalId(articleId, 100));
  return adapt(request(`/api/v1/documents/${encodeURIComponent(documentId)}?articleId=${encodeURIComponent(articleId)}`, { signal, timeoutMs: 15000 }), (value) => {
    const a = object(value, ["documentId", "documentTitle", "articleId", "article", "content", "sourceUrl"]);
    requireValue(a.documentId === documentId && a.articleId === articleId && text(a.documentTitle, 500)
      && text(a.article, 100) && text(a.content, 200000) && httpsUrl(a.sourceUrl));
    return { document_id: documentId, article_id: articleId, document_title: a.documentTitle,
      article: a.article, content: a.content, source_url: a.sourceUrl };
  });
}
