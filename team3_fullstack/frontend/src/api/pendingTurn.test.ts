import { afterEach, beforeEach, expect, it, vi } from "vitest";
import { forgetTurn, pendingFor, pendingTurns, rememberTurn } from "./pendingTurn";
let values: Map<string,string>;
const turn = { requestId: "44444444-4444-4444-8444-444444444444", question: "Câu hỏi" };
beforeEach(() => { values = new Map(); vi.stubGlobal("sessionStorage", { getItem: (k:string) => values.get(k) ?? null, setItem: (k:string,v:string) => values.set(k,v), removeItem: (k:string) => values.delete(k) }); });
afterEach(() => vi.unstubAllGlobals());
it("retains the original UUID/question before meta for reload/replay", () => {
  rememberTurn(turn); expect(pendingFor()).toEqual(turn);
});
it("binds meta to the existing receipt without a second turn", () => {
  rememberTurn(turn); rememberTurn({ ...turn, conversationId: "101" });
  expect(pendingFor()).toBeUndefined(); expect(pendingTurns()).toHaveLength(1); expect(pendingFor("101")?.requestId).toBe(turn.requestId);
});
it("removes question and receipt after a known terminal", () => {
  rememberTurn(turn); forgetTurn(turn.requestId); expect(pendingTurns()).toEqual([]); expect([...values.values()].join("")).not.toContain("Câu hỏi");
});
it("keeps receipts of other conversations while reconciling one", () => {
  rememberTurn(turn); rememberTurn({ requestId: "55555555-5555-4555-8555-555555555555", question: "Q2", conversationId: "202" });
  forgetTurn(turn.requestId); expect(pendingFor("202")?.question).toBe("Q2");
});
it("ignores corrupt or malformed storage instead of creating a new UUID", () => {
  values.set("legal-rag.pending-turns.v2", "bad-json"); expect(pendingTurns()).toEqual([]);
  values.set("legal-rag.pending-turns.v2", JSON.stringify([{ ...turn, conversationId: "uuid" }])); expect(pendingTurns()).toEqual([]);
});
it("disabled storage does not stop the current tab from sending", () => {
  vi.stubGlobal("sessionStorage", { getItem: () => { throw new Error("blocked"); }, setItem: () => { throw new Error("blocked"); } });
  expect(() => rememberTurn(turn)).not.toThrow(); expect(pendingTurns()).toEqual([]);
});
