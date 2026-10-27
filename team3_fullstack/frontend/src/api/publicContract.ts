import type { ChatComplete, ChatMeta, PublicCitation } from "../types/publicApi";

export function requireValue(condition: unknown): asserts condition {
  if (!condition) throw new Error("Invalid public API contract");
}
export function object(value: unknown, keys: string[]): Record<string, unknown> {
  requireValue(value !== null && typeof value === "object" && !Array.isArray(value));
  const record = value as Record<string, unknown>;
  requireValue(Object.keys(record).length === keys.length && keys.every((key) => Object.prototype.hasOwnProperty.call(record, key)));
  return record;
}
export function safeId(value: unknown): value is number {
  return typeof value === "number" && Number.isSafeInteger(value) && value > 0;
}
export function text(value: unknown, max: number): value is string {
  return typeof value === "string" && value.trim().length > 0 && Array.from(value).length <= max;
}
export function uuid(value: unknown): value is string {
  return typeof value === "string" && /^[\da-f]{8}-[\da-f]{4}-4[\da-f]{3}-[89ab][\da-f]{3}-[\da-f]{12}$/i.test(value);
}
export function timestamp(value: unknown): value is string {
  return typeof value === "string" && /^\d{4}-\d\d-\d\dT.*Z$/.test(value) && Number.isFinite(Date.parse(value));
}
export function legalId(value: unknown, max: number): value is string {
  return text(value, max) && /^[A-Za-z0-9_-]+$/.test(value);
}
export function httpsUrl(value: unknown): value is string {
  if (!text(value, 2048)) return false;
  try { const url = new URL(value); return url.protocol === "https:" && !!url.hostname; } catch { return false; }
}
export function parseCitation(value: unknown): PublicCitation {
  const c = object(value, ["citationId", "chunkId", "documentId", "articleId", "documentTitle", "article", "clause", "point", "sourceUrl"]);
  requireValue(typeof c.citationId === "string" && /^C(?:[1-9]|10)$/.test(c.citationId));
  requireValue(text(c.chunkId, 200) && legalId(c.documentId, 200) && legalId(c.articleId, 100));
  requireValue(text(c.documentTitle, 500) && text(c.article, 100));
  requireValue((c.clause === null || text(c.clause, 100)) && (c.point === null || text(c.point, 100)) && httpsUrl(c.sourceUrl));
  return c as unknown as PublicCitation;
}
const metaKeys = ["conversationId", "clientRequestId", "userMessageId", "assistantMessageId", "createdAt"];
function checkMeta(m: Record<string, unknown>) {
  requireValue(safeId(m.conversationId) && uuid(m.clientRequestId) && safeId(m.userMessageId) && safeId(m.assistantMessageId));
  requireValue(m.userMessageId !== m.assistantMessageId && timestamp(m.createdAt));
}
export function parseMeta(value: unknown): ChatMeta {
  const m = object(value, metaKeys); checkMeta(m); return m as unknown as ChatMeta;
}
export function checkAnswer(status: unknown, answer: unknown, citations: unknown): asserts citations is PublicCitation[] {
  requireValue((status === "answered" || status === "insufficient_context") && text(answer, 12000) && Array.isArray(citations));
  citations.forEach(parseCitation);
  const mentions = [...new Set([...answer.matchAll(/\[C(\d+)\]/g)].map((m) => `C${m[1]}`))];
  if (status === "insufficient_context") { requireValue(citations.length === 0 && mentions.length === 0); return; }
  requireValue(citations.length >= 1 && citations.length <= 10);
  const expected = citations.map((_, i) => `C${i + 1}`);
  requireValue(JSON.stringify(mentions) === JSON.stringify(expected));
  requireValue(new Set(citations.map((c) => c.chunkId)).size === citations.length);
  requireValue(new Set(citations.map((c) => c.citationId)).size === citations.length && expected.every((id) => citations.some((c) => c.citationId === id)));
}
export function parseComplete(value: unknown, meta: ChatMeta): ChatComplete {
  const c = object(value, [...metaKeys, "status", "answer", "citations"]); checkMeta(c);
  requireValue(metaKeys.every((key) => c[key] === meta[key as keyof ChatMeta]));
  checkAnswer(c.status, c.answer, c.citations);
  return c as unknown as ChatComplete;
}
export function errorDetail(value: unknown) {
  const e = object(object(value, ["error"]).error, ["code", "message", "retryable"]);
  requireValue(text(e.code, 60) && text(e.message, 2000) && typeof e.retryable === "boolean");
  return e as { code: string; message: string; retryable: boolean };
}
