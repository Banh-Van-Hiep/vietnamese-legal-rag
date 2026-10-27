import { afterEach, expect, it, vi } from "vitest";
import { numericId, v2Article, v2Conversations, v2Messages } from "./publicApi";
const timestamp = "2026-10-23T00:00:00Z";
const stub = (value: unknown) => vi.stubGlobal("fetch", vi.fn(async () => new Response(JSON.stringify(value), { headers: { "Content-Type": "application/json" } })));
afterEach(() => vi.unstubAllGlobals());
it("loads conversation arrays without pagination and maps to presentation model", async () => {
  stub([{ id: 101, title: "Hội thoại", createdAt: timestamp, updatedAt: timestamp }]);
  await expect(v2Conversations()).resolves.toEqual([{ conversation_id: "101", title: "Hội thoại", created_at: timestamp, updated_at: timestamp }]);
  expect(vi.mocked(fetch).mock.calls[0][0]).toMatch(/\/api\/v1\/conversations$/);
});
it("rejects legacy pages or UUIDs in public IDs", async () => {
  for (const bad of [{ items: [] }, [{ id: "uuid", title: "T", createdAt: timestamp, updatedAt: timestamp }]]) {
    stub(bad); await expect(v2Conversations()).rejects.toMatchObject({ code: "INVALID_RESPONSE_BODY" });
  }
});
it("preserves pending/failed states when loading messages", async () => {
  const base = { conversationId: 101, clientRequestId: "44444444-4444-4444-8444-444444444444", role: "assistant", content: null, answerStatus: null, citations: [], createdAt: timestamp };
  stub([{ ...base, id: 202, sequenceNo: 2, state: "failed", errorCode: "SERVICE_UNAVAILABLE" }, { ...base, id: 204, sequenceNo: 4, state: "pending", errorCode: null }]);
  const result = await v2Messages("101"); expect(result.map((m) => m.state)).toEqual(["failed", "pending"]);
  expect(vi.mocked(fetch).mock.calls[0][0]).toMatch(/\/101\/messages$/);
});
it("rejects history from another conversation or unordered sequences", async () => {
  const base = { id: 201, conversationId: 999, clientRequestId: "44444444-4444-4444-8444-444444444444", sequenceNo: 1, role: "user", state: "completed", content: "Q", answerStatus: null, citations: [], errorCode: null, createdAt: timestamp };
  stub([base]); await expect(v2Messages("101")).rejects.toMatchObject({ code: "INVALID_RESPONSE_BODY" });
  stub([{ ...base, conversationId: 101 }, { ...base, id: 202, conversationId: 101 }]);
  await expect(v2Messages("101")).rejects.toMatchObject({ code: "INVALID_RESPONSE_BODY" });
});
it("uses document query route and verifies exact source version/ID", async () => {
  const article = { documentId: "doc_v1", documentTitle: "Văn bản", articleId: "art1", article: "Điều 1", content: "Nguyên văn 😀", sourceUrl: "https://example.com/source" };
  stub(article); expect((await v2Article("doc_v1", "art1")).content).toBe("Nguyên văn 😀");
  expect(vi.mocked(fetch).mock.calls[0][0]).toMatch(/\/documents\/doc_v1\?articleId=art1$/);
  stub({ ...article, documentId: "doc_v2" }); await expect(v2Article("doc_v1", "art1")).rejects.toMatchObject({ code: "INVALID_RESPONSE_BODY" });
});
it("does not silently coerce a malformed route ID", () => {
  for (const id of ["0", "-1", "1.0", "1e2", "1x", "9007199254740992"]) expect(() => numericId(id)).toThrow();
});
