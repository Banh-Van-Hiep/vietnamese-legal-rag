import { afterEach, describe, expect, it, vi } from "vitest";
import { renderToStaticMarkup } from "react-dom/server";
import DebugLatencyBadge from "./DebugLatencyBadge";
import MessageBubble from "./MessageBubble";
import type { UiMessage } from "../../types";

afterEach(() => vi.unstubAllEnvs());
const message: UiMessage = { key: "a", role: "assistant", state: "completed", content: "Kết quả thử nghiệm.",
  answerStatus: "answered", citations: [], responseTimeMs: 1234 };
const render = (m: UiMessage) => renderToStaticMarkup(<MessageBubble message={m} isLast onRetry={() => {}} onOpenCitation={() => {}} />);
function enable() { vi.stubEnv("DEV", true); vi.stubEnv("VITE_DEBUG_LATENCY", "true"); }
describe("debug response timing", () => {
  it("shows contextual timing only for a completed assistant with an observed value", () => {
    enable(); expect(render(message)).toContain("1,23 s");
    expect(render({ ...message, responseTimeMs: undefined })).not.toContain('data-testid="latency-badge"');
    expect(render({ ...message, role: "user" })).not.toContain('data-testid="latency-badge"');
  });
  it("hides timing for pending and failed attempts even if an obsolete value is present", () => {
    enable();
    for (const state of ["pending", "failed"] as const)
      expect(render({ ...message, state })).not.toContain('data-testid="latency-badge"');
  });
  it("is hidden by default and in production even with the flag enabled", () => {
    vi.stubEnv("DEV", true); vi.stubEnv("VITE_DEBUG_LATENCY", "false");
    expect(render(message)).not.toContain('data-testid="latency-badge"');
    vi.stubEnv("DEV", false); vi.stubEnv("VITE_DEBUG_LATENCY", "true");
    expect(render(message)).not.toContain('data-testid="latency-badge"');
  });
  it("does not display invalid or negative duration values", () => {
    enable();
    for (const elapsedMs of [NaN, Infinity, -1])
      expect(renderToStaticMarkup(<DebugLatencyBadge elapsedMs={elapsedMs} />)).toBe("");
  });
});
