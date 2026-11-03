/** Team 3: real-corpus Viewer and configurable G4 preparation. No inference is simulated in live mode. */
import assert from 'node:assert/strict';
import { readFile, writeFile, mkdir } from 'node:fs/promises';
import path from 'node:path';
import { spawn } from 'node:child_process';

const { FE_URL: fe, BE_URL: be, RAG_URL: rag, CDP_URL: cdp, EVIDENCE_DIR: out } = process.env;
const mode = process.env.ACCEPTANCE_MODE ?? 'corpus';
const fixture = JSON.parse(await readFile(process.env.ARTICLE_EXPECTED, 'utf8'));
const questions = process.env.QUESTIONS_FILE ? JSON.parse(await readFile(process.env.QUESTIONS_FILE, 'utf8')) : null;
await mkdir(out, { recursive: true });
const page = await (await fetch(cdp + '/json/new?about:blank', { method: 'PUT' })).json();
const ws = new WebSocket(page.webSocketDebuggerUrl);
await new Promise((resolve, reject) => { ws.onopen = resolve; ws.onerror = reject; });
let sequence = 0;
const pending = new Map(), results = [], exceptions = [], requests = [];
let recording = null;
ws.onmessage = ({ data }) => {
  const message = JSON.parse(data);
  if (message.id) {
    const entry = pending.get(message.id);
    if (!entry) return;
    pending.delete(message.id); clearTimeout(entry.timer);
    message.error ? entry.reject(new Error(JSON.stringify(message.error))) : entry.resolve(message.result);
  } else if (message.method === 'Runtime.exceptionThrown') {
    exceptions.push(message.params.exceptionDetails);
  } else if (message.method === 'Network.requestWillBeSent') {
    const request = message.params.request;
    if (request.method === 'POST' && request.url.endsWith('/api/v1/chat/stream') && request.postData) {
      requests.push(JSON.parse(request.postData));
    }
  }
};
function command(method, params = {}) {
  return new Promise((resolve, reject) => {
    const id = ++sequence;
    const timer = setTimeout(() => { pending.delete(id); reject(new Error('CDP timeout: ' + method)); }, 20000);
    pending.set(id, { resolve, reject, timer }); ws.send(JSON.stringify({ id, method, params }));
  });
}
async function evaluate(expression) {
  const result = await command('Runtime.evaluate', { expression, awaitPromise: true, returnByValue: true });
  if (result.exceptionDetails) throw new Error(JSON.stringify(result.exceptionDetails));
  return result.result.value;
}
const pause = ms => new Promise(resolve => setTimeout(resolve, ms));
async function until(expression, timeout = 20000) {
  const deadline = Date.now() + timeout;
  while (Date.now() < deadline) { const value = await evaluate(expression); if (value) return value; await pause(40); }
  throw new Error('Browser deadline: ' + expression);
}
async function route(url) {
  await evaluate(`history.pushState({},'',${JSON.stringify(url)});dispatchEvent(new PopStateEvent('popstate'))`);
}
async function screenshot(name) {
  const shot = await command('Page.captureScreenshot', { format: 'png' });
  await writeFile(path.join(out, name + '.png'), Buffer.from(shot.data, 'base64'));
}
function startRecording() {
  if (!process.env.FFMPEG_PATH) return;
  const file = path.join(out, 'g4-demo.mp4');
  const proc = spawn(process.env.FFMPEG_PATH, ['-hide_banner', '-loglevel', 'error', '-f', 'image2pipe',
    '-vcodec', 'mjpeg', '-framerate', '2', '-i', 'pipe:0', '-an', '-c:v', 'libx264',
    '-preset', 'veryfast', '-pix_fmt', 'yuv420p', file], { windowsHide: true });
  const state = { active: true, error: null, frames: 0, file };
  proc.on('error', error => { state.error = error; });
  proc.stdin.on('error', error => { state.error = error; });
  let stderr = '';
  proc.stderr.on('data', data => { stderr = (stderr + data).slice(-2000); });
  const exited = new Promise(resolve => proc.on('close', code => resolve(code)));
  state.loop = (async () => {
    while (state.active && !state.error) {
      const started = Date.now();
      try {
        const shot = await command('Page.captureScreenshot', { format: 'jpeg', quality: 75 });
        proc.stdin.write(Buffer.from(shot.data, 'base64')); state.frames++;
      } catch (error) { state.error = error; }
      await pause(Math.max(0, 500 - (Date.now() - started)));
    }
  })();
  recording = { state, proc, exited, stderr: () => stderr };
}
async function stopRecording() {
  if (!recording) return null;
  const { state, proc, exited, stderr } = recording;
  state.active = false; await state.loop; proc.stdin.end();
  const code = await exited;
  return { file: 'g4-demo.mp4', frames: state.frames, fps: 2, status: code === 0 && !state.error ? 'PASS' : 'FAIL',
    ...(code === 0 && !state.error ? {} : { error: String(state.error ?? stderr()) }) };
}
async function run(id, fn) {
  try { const detail = await fn(); results.push({ id, status: 'PASS', detail }); }
  catch (error) {
    results.push({ id, status: 'FAIL', error: String(error) });
    await screenshot('failure-' + id).catch(() => {});
    throw error;
  }
  finally { if (recording && id.startsWith('G4_')) await pause(1500); }
}
async function ask(question) {
  await evaluate(`(()=>{const e=document.querySelector('textarea');Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype,'value').set.call(e,${JSON.stringify(question)});e.dispatchEvent(new Event('input',{bubbles:true}));})()`);
  await until("!!document.querySelector('button[type=submit]:not(:disabled)')");
  await evaluate("document.querySelector('button[type=submit]').click()");
}
function complete(wire) {
  const frames = wire.replaceAll('\r\n', '\n').split('\n\n');
  for (const frame of frames) {
    if (/^event:\s*complete$/m.test(frame)) return JSON.parse(frame.split('\n').filter(x => x.startsWith('data:')).map(x => x.slice(5).trim()).join('\n'));
  }
  throw new Error('No complete frame');
}
try {
  await command('Page.enable'); await command('Runtime.enable'); await command('Network.enable');
  // Functional probe isolates external fonts; it does not claim full-page load performance.
  await command('Network.setBlockedURLs', { urls: ['*fonts.googleapis.com*', '*fonts.gstatic.com*'] });
  await command('Network.setCacheDisabled', { cacheDisabled: true });
  await command('Page.navigate', { url: fe + '/' });
  await until("!!document.querySelector('textarea')");
  const articleRoute = '/documents/' + encodeURIComponent(fixture.document_id) + '?articleId=' + encodeURIComponent(fixture.article_id);
  await run('CORPUS_CONTENT', async () => {
    await route(articleRoute); await until("!!document.querySelector('[data-testid=article-content]')");
    const value = await evaluate(`(()=>{const a=document.querySelector('[data-testid=source-link]');return {content:document.querySelector('[data-testid=article-content]').textContent,title:document.querySelector('[data-testid=article-document]').textContent,article:document.querySelector('[data-testid=article-title]').textContent,url:a.href,target:a.target,rel:a.rel}})()`);
    assert.equal(value.content, fixture.content); assert.equal(value.title, fixture.document_title);
    assert.equal(value.article, fixture.article); assert.equal(value.url, fixture.source_url);
    assert.equal(value.target, '_blank'); assert.ok(value.rel.includes('noopener') && value.rel.includes('noreferrer'));
    return { documentId: fixture.document_id, articleId: fixture.article_id, contentCharacters: value.content.length, contentAndSourcePreserved: true };
  });
  await run('CORPUS_TIMING', async () => {
    const samples = [];
    for (let i = 0; i < 20; i++) {
      await route('/'); await until("!document.querySelector('[data-testid=article-content]')");
      const elapsed = await evaluate(`(async()=>{const start=performance.now();history.pushState({},'',${JSON.stringify(articleRoute)});dispatchEvent(new PopStateEvent('popstate'));await new Promise((ok,no)=>{const timer=setTimeout(()=>{observer.disconnect();no(new Error('Article deadline'));},5000);const observer=new MutationObserver(()=>{if(document.querySelector('[data-testid=article-content]')){clearTimeout(timer);observer.disconnect();ok();}});observer.observe(document.body,{childList:true,subtree:true});});return performance.now()-start})()`);
      samples.push(elapsed);
    }
    const sorted = [...samples].sort((a, b) => a - b);
    const timing = { samplesMs: samples, p50Ms: sorted[9], p95Ms: sorted[18], maxMs: sorted[19], measure: 'SPA route action to article DOM; app ready; real corpus/HTTP; fonts isolated' };
    assert.ok(timing.p95Ms < 1000, JSON.stringify(timing)); return timing;
  });
  for (const width of [360, 768]) await run('CORPUS_VIEWPORT_' + width, async () => {
    await command('Emulation.setDeviceMetricsOverride', { width, height: 900, deviceScaleFactor: 1, mobile: false });
    await route(articleRoute); await until("!!document.querySelector('[data-testid=article-content]')");
    const metric = await evaluate('({width:innerWidth,scroll:document.documentElement.scrollWidth})');
    assert.ok(metric.scroll <= width + 1, JSON.stringify(metric)); await screenshot('viewer-' + width); return metric;
  });
  await run('CORPUS_404', async () => {
    const errors = [];
    for (const [document, article, code] of [['missing-document-v1', 'dieu-1', 'DOCUMENT_NOT_FOUND'], [fixture.document_id, 'dieu-999999', 'ARTICLE_NOT_FOUND']]) {
      const response = await fetch(be + '/api/v1/documents/' + document + '?articleId=' + article);
      assert.equal(response.status, 404); assert.equal((await response.json()).error.code, code); errors.push(code);
      await route('/documents/' + document + '?articleId=' + article);
      await until("!!document.querySelector('[data-testid=notice-info]')");
      assert.equal(await evaluate("!!document.querySelector('[data-testid=article-content]')"), false);
    }
    return { errors };
  });
  if (mode !== 'corpus') {
    const ready = await fetch(rag + '/internal/v1/ready');
    assert.ok(ready.ok); assert.equal(ready.headers.get('x-rag-mode') === 'mock', mode === 'mock-demo');
    assert.ok(questions?.answered && questions?.insufficient_context);
    await command('Emulation.setDeviceMetricsOverride', { width: 1280, height: 900, deviceScaleFactor: 1, mobile: false });
    startRecording();
    let firstRequest, canonical;
    await run('G4_P0_CITATION', async () => {
      await route('/'); await until("!!document.querySelector('textarea')"); await ask(questions.answered);
      await until("!!document.querySelector('[data-testid=cite-ref],[data-testid=notice-error]')", 65000);
      assert.equal(await evaluate("document.querySelector('[data-testid=notice-error]')?.innerText ?? null"), null);
      firstRequest = requests.at(-1); assert.ok(firstRequest);
      const id = await evaluate("location.pathname.match(/\\/c\\/(\\d+)/)?.[1]");
      const rows = await (await fetch(be + '/api/v1/conversations/' + id + '/messages')).json();
      assert.equal(rows.length, 2); assert.equal(rows[1].answerStatus, 'answered'); canonical = rows;
      await writeFile(path.join(out, 'g4-answered.json'), JSON.stringify({ request: firstRequest, messages: rows }, null, 2));
      await evaluate("document.querySelector('[data-testid=cite-ref]').click()");
      await until("!!document.querySelector('[data-testid=article-content]')"); await screenshot('g4-p0-viewer');
      return { conversationId: Number(id), citationCount: rows[1].citations.length };
    }).catch(() => {});
    if (canonical) await run('G4_REPLAY', async () => {
      const before = await (await fetch(be + '/api/v1/conversations/' + canonical[0].conversationId + '/messages')).json();
      const response = await fetch(be + '/api/v1/chat/stream', { method: 'POST', headers: { 'Content-Type': 'application/json', Accept: 'text/event-stream' }, body: JSON.stringify(firstRequest) });
      assert.equal(response.status, 200); const replay = complete(await response.text());
      assert.equal(replay.assistantMessageId, before[1].id);
      assert.equal(replay.answer, before[1].content);
      const after = await (await fetch(be + '/api/v1/conversations/' + replay.conversationId + '/messages')).json();
      assert.deepEqual(after, before); await screenshot('g4-replay'); return { noDuplicateMessages: true, sameUuid: firstRequest.clientRequestId };
    }).catch(() => {});
    else results.push({ id: 'G4_REPLAY', status: 'SKIP', reason: 'No completed P0 request available to replay' });
    await run('G4_INSUFFICIENT', async () => {
      await route('/'); await until("!!document.querySelector('textarea')"); await ask(questions.insufficient_context);
      await until("!!document.querySelector('[data-testid=notice-info],[data-testid=notice-error]')", 65000);
      assert.equal(await evaluate("document.querySelector('[data-testid=notice-error]')?.innerText ?? null"), null);
      assert.equal(await evaluate("document.querySelectorAll('[data-testid=cite-ref]').length"), 0);
      const id = await evaluate("location.pathname.match(/\\/c\\/(\\d+)/)?.[1]");
      const rows = await (await fetch(be + '/api/v1/conversations/' + id + '/messages')).json();
      assert.equal(rows.at(-1).answerStatus, 'insufficient_context'); await screenshot('g4-insufficient');
      await writeFile(path.join(out, 'g4-insufficient.json'), JSON.stringify(rows, null, 2));
      return { noCitations: true };
    }).catch(() => {});
  }
  assert.equal(exceptions.length, 0);
} finally {
  const video = await stopRecording();
  const report = { mode, articleSource: 'real corpus via Python/Java', liveG4Approved: false, passed: results.filter(r => r.status === 'PASS').length, total: results.length, results, exceptions, video };
  await writeFile(path.join(out, 'browser-results.json'), JSON.stringify(report, null, 2));
  console.log(JSON.stringify({ mode, passed: report.passed, total: report.total }));
  ws.close(); if (results.some(r => r.status !== 'PASS') || exceptions.length || video?.status === 'FAIL') process.exitCode = 1;
}
