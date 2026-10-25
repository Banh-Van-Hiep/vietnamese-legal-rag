/** VLRA-44 — E2E React → Java (profile rag, PostgreSQL) → FastAPI của Team 2 (HTTP mock).
 * Khác vlra42-smoke.mjs: không dùng rag-stub.mjs mà chạy chính service Python của Team 2
 * (team2_rag.api.mock_app), bật/tắt service để kiểm tra lỗi upstream. Chưa phải live RAG.
 * Cách chạy: scripts/run-vlra44-e2e.ps1 hoặc quickstart của VLRA-44. */
import assert from "node:assert/strict";
import { spawn, spawnSync } from "node:child_process";
import { mkdir, writeFile } from "node:fs/promises";
import path from "node:path";

const frontend = process.env.FE_URL ?? "http://127.0.0.1:15173";
const backend = process.env.BE_URL ?? "http://127.0.0.1:18043";
const ragPort = Number(process.env.RAG_PORT ?? 18044);
const rag = `http://127.0.0.1:${ragPort}`;
const cdp = process.env.CDP_URL ?? "http://127.0.0.1:19242";
const python = process.env.PYTHON ?? "python";
const repoRoot = path.resolve(process.env.REPO_ROOT ?? "../..");
const out = process.env.EVIDENCE_DIR ?? "../backend/target/vlra44-e2e";
await mkdir(out, { recursive: true });

const pause = (ms) => new Promise((r) => setTimeout(r, ms));
const logs = [];
let ragProcess = null;

/** Chạy FastAPI mock của Team 2 với kịch bản RAG_MOCK_SCENARIO; chờ /ready. */
async function startRag(scenario) {
  await stopRag();
  ragProcess = spawn(python, ["-m", "uvicorn", "team2_rag.api.mock_app:create_mock_app", "--factory",
    "--host", "127.0.0.1", "--port", String(ragPort), "--workers", "1"],
    { cwd: repoRoot, env: { ...process.env, RAG_MOCK_SCENARIO: scenario }, stdio: ["ignore", "pipe", "pipe"] });
  const tag = `[rag:${scenario}]`;
  ragProcess.stdout.on("data", (d) => logs.push(`${tag} ${d}`));
  ragProcess.stderr.on("data", (d) => logs.push(`${tag} ${d}`));
  const end = Date.now() + 30000;
  while (Date.now() < end) {
    try {
      const r = await fetch(`${rag}/internal/v1/ready`);
      if (r.ok) { assert.equal(r.headers.get("x-rag-mode"), "mock"); return; }
    } catch { /* chưa lên */ }
    if (ragProcess.exitCode !== null) throw new Error(`FastAPI mock thoát sớm:\n${logs.slice(-20).join("")}`);
    await pause(250);
  }
  throw new Error(`FastAPI mock không sẵn sàng sau 30s:\n${logs.slice(-20).join("")}`);
}
async function stopRag() {
  if (!ragProcess || ragProcess.exitCode !== null) { ragProcess = null; return; }
  if (process.platform === "win32") spawnSync("taskkill", ["/PID", String(ragProcess.pid), "/T", "/F"]);
  else ragProcess.kill("SIGTERM");
  const end = Date.now() + 10000;
  while (Date.now() < end) {
    try { await fetch(`${rag}/internal/v1/health`); } catch { ragProcess = null; return; }
    await pause(200);
  }
  throw new Error("Không dừng được FastAPI mock");
}

// --- CDP tới Edge/Chrome headless, cùng cách với vlra42-smoke.mjs ---
const target = await (await fetch(`${cdp}/json/new?about:blank`, { method: "PUT" })).json();
const ws = new WebSocket(target.webSocketDebuggerUrl);
await new Promise((resolve, reject) => { ws.onopen = resolve; ws.onerror = reject; });
let sequence = 0;
const pending = new Map(), requests = [], exceptions = [], results = [];
function command(method, params = {}) {
  const id = ++sequence;
  return new Promise((resolve, reject) => {
    const timer = setTimeout(() => { pending.delete(id); reject(new Error(`CDP timeout ${method}`)); }, 20000);
    pending.set(id, { resolve, reject, timer });
    ws.send(JSON.stringify({ id, method, params }));
  });
}
ws.onmessage = ({ data }) => {
  const m = JSON.parse(data);
  if (m.id) {
    const p = pending.get(m.id); if (!p) return;
    pending.delete(m.id); clearTimeout(p.timer);
    m.error ? p.reject(new Error(JSON.stringify(m.error))) : p.resolve(m.result);
    return;
  }
  if (m.method === "Runtime.exceptionThrown") exceptions.push(m.params.exceptionDetails);
  if (m.method === "Network.requestWillBeSent" && m.params.request.method === "POST"
      && m.params.request.url === `${backend}/api/v1/chat/stream`) {
    requests.push(JSON.parse(m.params.request.postData));
  }
};
async function evaluate(expression) {
  const r = await command("Runtime.evaluate", { expression, awaitPromise: true, returnByValue: true });
  if (r.exceptionDetails) throw new Error(JSON.stringify(r.exceptionDetails));
  return r.result.value;
}
async function until(expression, timeout = 20000) {
  const end = Date.now() + timeout;
  while (Date.now() < end) { const v = await evaluate(expression); if (v) return v; await pause(100); }
  throw new Error(`Hết thời gian chờ: ${expression}\n${await evaluate("document.body.innerText")}`);
}
const count = (selector) => evaluate(`document.querySelectorAll(${JSON.stringify(selector)}).length`);
const text = (selector) => evaluate(`document.querySelector(${JSON.stringify(selector)})?.textContent ?? ""`);
async function open(route = "/") {
  await command("Page.navigate", { url: frontend + route });
  await until("document.readyState==='complete'");
  await pause(150);
}
async function ask(question) {
  await until("!!document.querySelector('textarea')");
  await evaluate(`(()=>{const e=document.querySelector('textarea');Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype,'value').set.call(e,${JSON.stringify(question)});e.dispatchEvent(new Event('input',{bubbles:true}));})()`);
  await until("!document.querySelector('[data-testid=send]').disabled");
  await evaluate("document.querySelector('[data-testid=send]').click()");
}
async function clickButton(label) {
  const sel = `Array.from(document.querySelectorAll('button')).find(b=>b.textContent.trim()===${JSON.stringify(label)}&&!b.disabled)`;
  await until(`!!${sel}`);
  await evaluate(`${sel}.click()`);
}
const conversationId = () => evaluate("(location.pathname.match(/^\\/c\\/(\\d+)$/)||[])[1]||null");
async function messages(id) {
  const r = await fetch(`${backend}/api/v1/conversations/${id}/messages`);
  assert.equal(r.status, 200);
  return r.json();
}
async function caseRun(id, name, body) {
  const started = Date.now();
  try {
    const detail = await body();
    results.push({ id, name, status: "PASS", ms: Date.now() - started, ...(detail ? { detail } : {}) });
    console.log(`PASS ${id} ${name}`);
  } catch (error) {
    results.push({ id, name, status: "FAIL", ms: Date.now() - started, message: String(error).slice(0, 2000) });
    console.log(`FAIL ${id} ${name}\n  ${String(error).split("\n")[0]}`);
  }
}

const suffix = Date.now().toString(36);
const MOCK_ANSWER = "câu trả lời giả lập";
const MOCK_ARTICLE = "nguyên văn Điều giả lập";
let conv;
try {
  await command("Runtime.enable"); await command("Network.enable"); await command("Page.enable");

  await caseRun("E01", "Ba service sẵn sàng: Java health, FastAPI mock ready", async () => {
    await startRag("answered");
    const health = await fetch(`${backend}/api/v1/health`);
    assert.equal(health.status, 200);
    return { backendHealth: health.status, ragMode: "mock" };
  });

  await caseRun("E02", "Hỏi lượt đầu: React → Java SSE → FastAPI, có câu trả lời và trích dẫn", async () => {
    await open("/");
    const q = `E2E lượt đầu ${suffix}`;
    await ask(q);
    await until(`(document.querySelector('[data-testid=answer]')?.textContent||'').includes(${JSON.stringify(MOCK_ANSWER)})`);
    conv = await until("(location.pathname.match(/^\\/c\\/(\\d+)$/)||[])[1]||null");
    assert.equal(await count("[data-testid=citation]"), 1);
    assert.equal(await count("[data-testid=cite-ref]"), 1);
    assert.ok(await count("[data-testid=mock-badge]") >= 1, "thiếu nhãn dữ liệu thử nghiệm");
    await until(`Array.from(document.querySelectorAll('aside a')).some(a=>a.textContent.includes(${JSON.stringify(q)}))`);
    return { conversationId: Number(conv) };
  });

  await caseRun("E03", "Bấm trích dẫn → Java proxy → FastAPI article, mở đúng nguyên văn", async () => {
    await evaluate("document.querySelector('[data-testid=cite-ref]').click()");
    await until("!!document.querySelector('[data-testid=article-content]')");
    assert.match(await text("[data-testid=article-content]"), new RegExp(MOCK_ARTICLE));
    assert.equal(await evaluate("document.querySelector('[data-testid=source-link]').getAttribute('href')"), "https://example.com/mock-law");
    const r = await fetch(`${backend}/api/v1/documents/mock_v1?articleId=art1`);
    assert.equal(r.status, 200);
    const body = await r.json();
    assert.deepEqual(Object.keys(body).sort(), ["article", "articleId", "content", "documentId", "documentTitle", "sourceUrl"]);
    await evaluate("document.dispatchEvent(new KeyboardEvent('keydown',{key:'Escape'}))");
    await until("!document.querySelector('[data-testid=drawer]')");
  });

  await caseRun("E04", "Hỏi tiếp cùng hội thoại: giữ conversationId, lưu đủ 4 tin nhắn", async () => {
    await ask(`E2E hỏi tiếp ${suffix}`);
    await until(`document.querySelectorAll('[data-testid=answer]').length===2`);
    assert.equal(await conversationId(), conv);
    const rows = await messages(conv);
    assert.equal(rows.length, 4);
    assert.deepEqual(rows.map((m) => m.role), ["user", "assistant", "user", "assistant"]);
    assert.ok(rows.every((m) => m.state === "completed"));
    const last = requests.at(-1);
    assert.equal(last.conversationId, Number(conv));
    return { messages: rows.length };
  });

  await caseRun("E05", "Tải lại hội thoại: lịch sử từ PostgreSQL, không gọi lại AI", async () => {
    const before = requests.length;
    await command("Page.reload");
    await until(`document.querySelectorAll('[data-testid=answer]').length===2`);
    assert.equal(requests.length, before, "reload không được gửi lại câu hỏi");
    assert.equal(await count("[data-testid=citation]"), 2);
  });

  await caseRun("E06", "Viewer 404 từ Python giữ nguyên mã DOCUMENT/ARTICLE_NOT_FOUND", async () => {
    const art = await fetch(`${backend}/api/v1/documents/mock_v1?articleId=art2`);
    assert.equal(art.status, 404);
    assert.equal((await art.json()).error.code, "ARTICLE_NOT_FOUND");
    const doc = await fetch(`${backend}/api/v1/documents/other_v1?articleId=art1`);
    assert.equal(doc.status, 404);
    assert.equal((await doc.json()).error.code, "DOCUMENT_NOT_FOUND");
    await open("/documents/mock_v1?articleId=art2");
    await until("(document.body.textContent||'').includes('Không mở được nguyên văn')");
  });

  await caseRun("E07", "insufficient_context từ FastAPI: thông báo riêng, không có trích dẫn", async () => {
    await startRag("insufficient_context");
    await open("/");
    await ask(`E2E thiếu căn cứ ${suffix}`);
    await until("(document.querySelector('[data-testid=notice-info]')?.textContent||'').includes('Chưa đủ căn cứ')");
    assert.equal(await count("[data-testid=citation]"), 0);
    assert.equal(await count("[data-testid=cite-ref]"), 0);
    const id = await until("(location.pathname.match(/^\\/c\\/(\\d+)$/)||[])[1]||null");
    const rows = await messages(id);
    assert.equal(rows.at(-1).answerStatus, "insufficient_context");
  });

  await caseRun("E08", "FastAPI ngừng: báo SERVICE_UNAVAILABLE, lưu lượt failed, giữ hội thoại", async () => {
    await stopRag();
    await open("/");
    await ask(`E2E dịch vụ ngừng ${suffix}`);
    await until("(document.querySelector('[data-testid=notice-error]')?.textContent||'').includes('SERVICE_UNAVAILABLE')");
    const id = await until("(location.pathname.match(/^\\/c\\/(\\d+)$/)||[])[1]||null");
    const rows = await messages(id);
    assert.equal(rows.at(-1).state, "failed");
    assert.equal(rows.at(-1).errorCode, "SERVICE_UNAVAILABLE");
    const viewer = await fetch(`${backend}/api/v1/documents/mock_v1?articleId=art1`);
    assert.equal(viewer.status, 503);
    return { conversationId: Number(id) };
  });

  await caseRun("E09", "Bật lại FastAPI và Thử lại: lượt mới UUID mới, có câu trả lời", async () => {
    await startRag("answered");
    const before = requests.length;
    await clickButton("Thử lại");
    await until(`(document.querySelector('[data-testid=answer]')?.textContent||'').includes(${JSON.stringify(MOCK_ANSWER)})`);
    const sent = requests.slice(before);
    assert.ok(sent.length >= 1);
    const failedId = requests[before - 1].clientRequestId;
    assert.notEqual(sent.at(-1).clientRequestId, failedId, "lỗi đã xác định phải dùng UUID mới");
    const rows = await messages(await conversationId());
    assert.deepEqual(rows.map((m) => `${m.role}:${m.state}`), ["user:completed", "assistant:failed", "user:completed", "assistant:completed"]);
  });

  await caseRun("E10", "Request public đúng v2.0: camelCase, UUID v4, không gửi history/scenario", async () => {
    assert.ok(requests.length >= 5);
    for (const body of requests) {
      assert.match(body.clientRequestId, /^[\da-f]{8}-[\da-f]{4}-4[\da-f]{3}-[89ab][\da-f]{3}-[\da-f]{12}$/i);
      assert.ok(!("history" in body) && !("scenario" in body));
      if (body.conversationId != null) assert.equal(typeof body.conversationId, "number");
    }
    assert.equal(exceptions.length, 0, JSON.stringify(exceptions).slice(0, 500));
    return { publicRequests: requests.length, uncaughtExceptions: exceptions.length };
  });

  const shot = await command("Page.captureScreenshot", { format: "png" });
  await writeFile(path.join(out, "browser.png"), Buffer.from(shot.data, "base64"));
} finally {
  await stopRag().catch(() => {});
  const passed = results.filter((r) => r.status === "PASS").length;
  await writeFile(path.join(out, "results.json"), JSON.stringify({
    task: "VLRA-44", level: "E2E với HTTP mock của Team 2 (G2); chưa phải live RAG",
    ranAt: new Date().toISOString(), frontend, backend, rag, passed, total: results.length,
    results, requests, exceptions,
  }, null, 2));
  await writeFile(path.join(out, "rag-mock.log"), logs.join(""));
  console.log(`\n${passed}/${results.length} PASS. Evidence: ${path.resolve(out)}`);
  await command("Page.close").catch(() => {});
  ws.close();
  process.exitCode = passed === results.length ? 0 : 1;
}
