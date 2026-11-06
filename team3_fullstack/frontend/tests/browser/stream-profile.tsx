/** TEST ONLY: actual ChatWindow, controlled history/100 deltas, no network/model. */
import React, { Profiler, useState, type ProfilerOnRenderCallback } from "react";
import { createRoot } from "react-dom/client";
import { flushSync } from "react-dom";
import ChatWindow from "../../src/components/chat/ChatWindow";
import type { Citation, UiMessage } from "../../src/types";
import "../../src/styles/global.css";

const citation: Citation = { citation_id: "C1", chunk_id: "profile-v1__dieu-1__k0__0",
  document_id: "profile-v1", article_id: "dieu-1", document_title: "Nguồn kiểm thử",
  article: "Điều 1", clause: null, point: null, source_url: "https://example.com/profile" };
const history: UiMessage[] = Array.from({ length: 20 }, (_, i) => [
  { key: "u" + i, role: "user" as const, state: "completed" as const, content: "Câu hỏi kiểm thử " + i, answerStatus: null, citations: [] },
  { key: "a" + i, role: "assistant" as const, state: "completed" as const,
    content: "**Nội dung kiểm thử**\n\n" + "Đối chiếu nguồn pháp lý và các điều kiện áp dụng. ".repeat(12) + "[C1]",
    answerStatus: "answered" as const, citations: [citation] },
]).flat();
const noop = () => {};
let update: React.Dispatch<React.SetStateAction<UiMessage[]>>;
let active = false;
let renders: { phase: string; actualMs: number; baseMs: number }[] = [];
const onRender: ProfilerOnRenderCallback = (_id, phase, actualMs, baseMs) => {
  if (active) renders.push({ phase, actualMs, baseMs });
};
function TestApp() {
  const [messages, setMessages] = useState(history); update = setMessages;
  return <Profiler id="chat-window" onRender={onRender}>
    <ChatWindow messages={messages} loading={false} onSuggestion={noop} onRetry={noop} onOpenCitation={noop} />
  </Profiler>;
}
createRoot(document.getElementById("root")!).render(<TestApp />);
const pause = (ms: number) => new Promise<void>(resolve => setTimeout(resolve, ms));
const nextFrame = () => new Promise<number>(resolve => requestAnimationFrame(resolve));
declare global { interface Window { runStreamProfile: () => Promise<unknown> } }
window.runStreamProfile = async () => {
  flushSync(() => update(history)); await nextFrame(); await nextFrame();
  renders = []; active = true;
  const frames: number[] = [], longTasks: number[] = [];
  let previous: number | undefined, recording = true;
  const tick = (time: number) => { if (previous !== undefined) frames.push(time - previous); previous = time; if (recording) requestAnimationFrame(tick); };
  requestAnimationFrame(tick);
  const observer = new PerformanceObserver(list => longTasks.push(...list.getEntries().map(e => e.duration)));
  observer.observe({ type: "longtask", buffered: false });
  const parts = Array.from({ length: 100 }, (_, i) => `Đoạn ${i} kiểm thử. `); parts[99] += "[C1]";
  update([...history,
    { key: "stream-user", role: "user", state: "completed", content: "Render fixture", answerStatus: null, citations: [] },
    { key: "stream-answer", role: "assistant", state: "pending", content: "", answerStatus: null, citations: [] }]);
  for (const part of parts) {
    await pause(8);
    update(all => all.map(m => m.key === "stream-answer" ? { ...m, content: m.content + part } : m));
  }
  update(all => all.map(m => m.key === "stream-answer"
    ? { ...m, state: "completed", content: parts.join(""), answerStatus: "answered", citations: [citation] } : m));
  await pause(200); active = false; recording = false; observer.disconnect();
  const bubble = document.querySelectorAll('[data-testid="msg-assistant"]');
  const last = bubble[bubble.length - 1];
  return { mode: "controlled React render fixture; no Backend or model", historyMessages: history.length, deltas: 100,
    commits: renders.length, renderSamples: renders, totalActualMs: renders.reduce((n, r) => n + r.actualMs, 0),
    maxActualMs: Math.max(...renders.map(r => r.actualMs)), framesMs: frames, longTasksMs: longTasks,
    exactFinalText: last?.querySelector('[data-testid="answer"]')?.textContent === parts.join("").replace("[C1]", "1"),
    finalCitations: last?.querySelectorAll('[data-testid="cite-ref"]').length };
};
