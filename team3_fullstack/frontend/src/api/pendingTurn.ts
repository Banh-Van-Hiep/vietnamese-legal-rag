import { numericId } from "./publicApi";
import { text, uuid } from "./publicContract";

export interface PendingTurn { requestId: string; question: string; conversationId?: string }
const KEY = "legal-rag.pending-turns.v2";
/** Only unresolved turn receipts; never stores API keys or the full conversation history. */
export function pendingTurns(): PendingTurn[] {
  try {
    const data: unknown = JSON.parse(sessionStorage.getItem(KEY) ?? "[]");
    if (!Array.isArray(data)) return [];
    return data.filter((v): v is PendingTurn => {
      if (!v || typeof v !== "object" || !uuid(v.requestId) || !text(v.question, 2000)) return false;
      if (v.conversationId !== undefined) {
        try { if (typeof v.conversationId !== "string") return false; numericId(v.conversationId); } catch { return false; }
      }
      return true;
    });
  } catch { return []; }
}
function write(turns: PendingTurn[]) {
  try { if (turns.length) sessionStorage.setItem(KEY, JSON.stringify(turns)); else sessionStorage.removeItem(KEY); }
  catch { /* Storage may be disabled; the current tab still retains the in-memory receipt. */ }
}
export function rememberTurn(turn: PendingTurn) { write([...pendingTurns().filter((v) => v.requestId !== turn.requestId), turn]); }
export function forgetTurn(id: string) { write(pendingTurns().filter((v) => v.requestId !== id)); }
export function pendingFor(conversationId?: string) { return pendingTurns().find((v) => v.conversationId === conversationId); }
