/** Actual UI/Java/PG lifecycle checks against labelled FastAPI fixture. */
import assert from 'node:assert/strict';
import { writeFile } from 'node:fs/promises';
import path from 'node:path';
const { FE_URL: fe, BE_URL: be, CDP_URL: cdp, EVIDENCE_DIR: out } = process.env;
const target = await (await fetch(cdp + '/json/new?about:blank', { method: 'PUT' })).json();
const ws = new WebSocket(target.webSocketDebuggerUrl);
await new Promise((resolve, reject) => { ws.onopen = resolve; ws.onerror = reject; });
let seq = 0; const pending = new Map(), requests = [], exceptions = [], results = [];
ws.onmessage = ({ data }) => {
  const m = JSON.parse(data);
  if (m.id) { const p = pending.get(m.id); if (p) { clearTimeout(p.timer); pending.delete(m.id); m.error ? p.reject(new Error(JSON.stringify(m.error))) : p.resolve(m.result); } }
  else if (m.method === 'Runtime.exceptionThrown') exceptions.push(m.params.exceptionDetails);
  else if (m.method === 'Network.requestWillBeSent' && m.params.request.url === be + '/api/v1/chat/stream' && m.params.request.postData)
    requests.push(JSON.parse(m.params.request.postData));
};
function command(method, params = {}) { return new Promise((resolve, reject) => {
  const id = ++seq, timer = setTimeout(() => { pending.delete(id); reject(new Error('CDP timeout ' + method)); }, 25000);
  pending.set(id, { resolve, reject, timer }); ws.send(JSON.stringify({ id, method, params }));
}); }
async function js(expression) {
  const r = await command('Runtime.evaluate', { expression, awaitPromise: true, returnByValue: true });
  if (r.exceptionDetails) throw new Error(JSON.stringify(r.exceptionDetails)); return r.result.value;
}
const pause = ms => new Promise(r => setTimeout(r, ms));
async function until(expression, timeout = 20000) {
  const end = Date.now() + timeout;
  while (Date.now() < end) { const r = await js(expression); if (r) return r; await pause(50); }
  throw new Error('UI deadline ' + expression);
}
async function open(route = '/') {
  await command('Page.navigate', { url: fe + route }); await until("!!document.querySelector('textarea')");
}
async function ask(question) {
  await js(`(()=>{const e=document.querySelector('textarea');Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype,'value').set.call(e,${JSON.stringify(question)});e.dispatchEvent(new Event('input',{bubbles:true}));})()`);
  await until("!document.querySelector('[data-testid=send]').disabled");
  await js("document.querySelector('[data-testid=send]').click()");
}
const noBadge = () => js("document.querySelectorAll('[data-testid=latency-badge]').length===0");
async function run(id, fn) {
  try { results.push({ id, status: 'PASS', detail: await fn() }); }
  catch (error) {
    const notice = await js("document.querySelector('[data-testid=notice-error]')?.textContent ?? null").catch(() => null);
    results.push({ id, status: 'FAIL', error: String(error), notice });
    const shot = await command('Page.captureScreenshot', { format: 'png' }).catch(() => null);
    if (shot) await writeFile(path.join(out, 'failure-' + id + '.png'), Buffer.from(shot.data, 'base64'));
    throw error;
  }
}
try {
  await command('Page.enable'); await command('Runtime.enable'); await command('Network.enable');
  await command('Network.setBlockedURLs', { urls: ['*fonts.googleapis.com*', '*fonts.gstatic.com*'] });
  await command('Emulation.setDeviceMetricsOverride', { width: 1280, height: 900, deviceScaleFactor: 1, mobile: false });
  await run('U01_DEBUG_COMPLETE_CITATION_HISTORY', async () => {
    await open(); assert.ok(await noBadge()); await ask('fixture-p0-week8');
    await until("!!document.querySelector('[data-testid=latency-badge]')");
    const badge = await js("document.querySelector('[data-testid=latency-badge]').textContent");
    assert.match(badge, /Phản hồi:.*s/);
    const request = requests.at(-1); assert.deepEqual(Object.keys(request).sort(), ['clientRequestId', 'question']);
    const route = await js('location.pathname');
    await js("document.querySelector('[data-testid=cite-ref]').click()");
    await until("!!document.querySelector('[data-testid=article-content]')");
    const shot = await command('Page.captureScreenshot', { format: 'png' });
    await writeFile(path.join(out, 'debug-latency-viewer.png'), Buffer.from(shot.data, 'base64'));
    await open(route); await until("!!document.querySelector('[data-testid=answer]')"); assert.ok(await noBadge());
    return { badge, historyDoesNotInventLatency: true, citationViewerOpened: true };
  });
  await run('U02_INSUFFICIENT_COMPLETE_TIMING', async () => {
    await open(); await ask('fixture-insufficient');
    await until("!!document.querySelector('[data-testid=notice-info]')");
    assert.equal(await js("document.querySelectorAll('[data-testid=cite-ref]').length"), 0);
    assert.equal(await noBadge(), false); return { completedWithoutCitation: true };
  });
  await run('U03_FAILED_ATTEMPT_NO_COMPLETED_TIMING', async () => {
    await open(); await ask('fixture-timeout-week8'); await until("!!document.querySelector('[data-testid=notice-error]')");
    assert.ok(await noBadge()); return { failedAttemptHasNoBadge: true };
  });
  await run('U04_SLOW3G_STOP_REPLAY_SAME_UUID', async () => {
    await open();
    await command('Network.emulateNetworkConditions', { offline: false, latency: 400, downloadThroughput: 50000,
      uploadThroughput: 50000, connectionType: 'cellular3g' });
    await ask('fixture-slow-stop-week8');
    await until("/^\\/c\\/\\d+$/.test(location.pathname)"); assert.ok(await noBadge());
    const original = requests.at(-1), id = await js("location.pathname.split('/').at(-1)");
    await js("[...document.querySelectorAll('button')].find(b=>b.textContent.trim()==='Dừng nhận').click()");
    await until("!!document.querySelector('[data-testid=notice-error]')"); assert.ok(await noBadge());
    const end = Date.now() + 10000;
    while (true) {
      const rows = await (await fetch(be + '/api/v1/conversations/' + id + '/messages')).json();
      if (rows.at(-1)?.state === 'completed') break;
      if (Date.now() > end) throw new Error('Server did not finish stopped turn'); await pause(100);
    }
    await js("document.querySelector('[data-testid=notice-error] button').click()");
    await until("!!document.querySelector('[data-testid=latency-badge]')");
    assert.equal(requests.at(-1).clientRequestId, original.clientRequestId);
    const rows = await (await fetch(be + '/api/v1/conversations/' + id + '/messages')).json();
    assert.equal(rows.length, 2); assert.equal(rows.at(-1).state, 'completed');
    await command('Network.emulateNetworkConditions', { offline: false, latency: 0, downloadThroughput: -1, uploadThroughput: -1 });
    return { sameUuid: true, messages: rows.length, simulatedLatencyMs: 400, throughputBytesPerSecond: 50000 };
  });
  await run('U05_NAVIGATION_DISCARDS_OLD_ATTEMPT', async () => {
    await open(); await ask('fixture-slow-navigation-week8');
    await until("/^\\/c\\/\\d+$/.test(location.pathname)");
    await js("document.querySelector('[data-testid=new-chat]').click()");
    await until("location.pathname==='/'"); await pause(4000);
    assert.equal(await js("document.querySelectorAll('[data-testid=msg-assistant]').length"), 0);
    assert.ok(await noBadge()); return { noOldResponseOrTimingOnNewRoute: true };
  });
  assert.equal(exceptions.length, 0);
} finally {
  await writeFile(path.join(out, 'ui-results.json'), JSON.stringify({ mode: 'real UI/Java/PG; HTTP fixture, not model',
    passed: results.filter(r => r.status === 'PASS').length, total: results.length, results, exceptions }, null, 2));
  await command('Page.close').catch(() => {}); ws.close();
}
