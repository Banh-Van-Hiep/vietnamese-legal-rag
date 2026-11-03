/** CDP profiling of real React components; no model or public API requests. */
import assert from 'node:assert/strict';
import { writeFile } from 'node:fs/promises';
import path from 'node:path';
const { FE_URL: fe, CDP_URL: cdp, EVIDENCE_DIR: out } = process.env;
const target = await (await fetch(cdp + '/json/new?about:blank', { method: 'PUT' })).json();
const ws = new WebSocket(target.webSocketDebuggerUrl);
await new Promise((resolve, reject) => { ws.onopen = resolve; ws.onerror = reject; });
let seq = 0; const pending = new Map(), exceptions = [];
ws.onmessage = ({ data }) => {
  const m = JSON.parse(data);
  if (m.id) { const p = pending.get(m.id); if (p) { clearTimeout(p.timer); pending.delete(m.id); m.error ? p.reject(new Error(JSON.stringify(m.error))) : p.resolve(m.result); } }
  else if (m.method === 'Runtime.exceptionThrown') exceptions.push(m.params.exceptionDetails);
};
function command(method, params = {}) { return new Promise((resolve, reject) => {
  const id = ++seq, timer = setTimeout(() => { pending.delete(id); reject(new Error('CDP timeout ' + method)); }, 30000);
  pending.set(id, { resolve, reject, timer }); ws.send(JSON.stringify({ id, method, params }));
}); }
async function js(expression) {
  const r = await command('Runtime.evaluate', { expression, awaitPromise: true, returnByValue: true });
  if (r.exceptionDetails) throw new Error(JSON.stringify(r.exceptionDetails)); return r.result.value;
}
try {
  await command('Page.enable'); await command('Runtime.enable'); await command('Network.enable');
  await command('Network.setBlockedURLs', { urls: ['*fonts.googleapis.com*', '*fonts.gstatic.com*'] });
  await command('Emulation.setDeviceMetricsOverride', { width: 1280, height: 900, deviceScaleFactor: 1, mobile: false });
  await command('Page.navigate', { url: fe + '/tests/browser/stream-profile.html' });
  const end = Date.now() + 30000;
  while (!(await js("document.querySelectorAll('[data-testid=msg-assistant]').length===20"))) {
    if (Date.now() > end) throw new Error('Profile entry did not load'); await new Promise(r => setTimeout(r, 100));
  }
  const samples = [];
  await js('window.runStreamProfile()'); // JIT warm-up, excluded from comparison.
  for (let i = 0; i < 3; i++) {
    const r = await js('window.runStreamProfile()');
    assert.equal(r.exactFinalText, true); assert.equal(r.finalCitations, 1); samples.push(r);
  }
  assert.equal(exceptions.length, 0);
  const report = { scope: 'development React Profiler; identical40 history messages/100 deltas; warm-up excluded', samples, exceptions };
  await writeFile(path.join(out, 'render-profile.json'), JSON.stringify(report, null, 2));
  console.log(JSON.stringify(samples.map(r => ({ commits: r.commits, totalActualMs: r.totalActualMs, maxActualMs: r.maxActualMs, longTasks: r.longTasksMs.length }))));
} finally { await command('Page.close').catch(() => {}); ws.close(); }
