/** Week10 actual React/Java/PG acceptance. Controlled faults are MOCK mode only. */
import assert from 'node:assert/strict';
import { readFile, writeFile, mkdir } from 'node:fs/promises';
import path from 'node:path';

const { FE_URL: fe, BE_URL: be, CDP_URL: cdp, EVIDENCE_DIR: out } = process.env;
const mode = process.env.ACCEPTANCE_MODE ?? 'mock';
assert.ok(fe && be && cdp && out, 'FE_URL, BE_URL, CDP_URL and EVIDENCE_DIR required');
assert.ok(['mock', 'corpus', 'live'].includes(mode), 'Unknown acceptance mode');
await mkdir(out, { recursive: true });
const expectedArticle = process.env.ARTICLE_EXPECTED
  ? JSON.parse(await readFile(process.env.ARTICLE_EXPECTED, 'utf8')) : null;
const expectedIds = mode === 'mock' ? Array.from({ length: 18 }, (_, i) => 'S' + String(i + 1).padStart(2, '0'))
  : mode === 'corpus' ? ['CORPUS_ARTICLE', 'CORPUS_FOCUS', 'CORPUS_SOURCE'] : ['LIVE_ANSWERED', 'LIVE_INSUFFICIENT'];
const results = [], exceptions = [], requests = [], articleRequests = [];
const articleRequestDetails = [];
const suffix = Date.now().toString(36);
const target = await (await fetch(cdp + '/json/new?about:blank', { method: 'PUT' })).json();
const ws = new WebSocket(target.webSocketDebuggerUrl);
await new Promise((resolve, reject) => { ws.onopen = resolve; ws.onerror = reject; });
let sequence = 0;
const pending = new Map();
let fault = null;
const pausedRequests = [];
const cancelledRequests = new Set();
const cancelledInterceptions = [];
const pause = ms => new Promise(resolve => setTimeout(resolve, ms));

function command(method, params = {}) {
  return new Promise((resolve, reject) => {
    const id = ++sequence;
    const timer = setTimeout(() => { pending.delete(id); reject(new Error('CDP deadline: ' + method)); }, 25000);
    pending.set(id, { resolve, reject, timer });
    ws.send(JSON.stringify({ id, method, params }));
  });
}
ws.onmessage = ({ data }) => {
  const m = JSON.parse(data);
  if (m.id) {
    const item = pending.get(m.id);
    if (!item) return;
    pending.delete(m.id); clearTimeout(item.timer);
    m.error ? item.reject(new Error(JSON.stringify(m.error))) : item.resolve(m.result);
    return;
  }
  if (m.method === 'Runtime.exceptionThrown') exceptions.push(m.params.exceptionDetails);
  if (m.method === 'Network.loadingFailed' && m.params.canceled) cancelledRequests.add(m.params.requestId);
  if (m.method === 'Network.requestWillBeSent') {
    const r = m.params.request;
    if (r.method === 'POST' && r.url === be + '/api/v1/chat/stream' && r.postData) requests.push(JSON.parse(r.postData));
    if (r.method === 'GET' && r.url.startsWith(be + '/api/v1/documents/')) {
      articleRequests.push(r.url); articleRequestDetails.push({ id: m.params.requestId, url: r.url });
    }
  }
  if (m.method === 'Fetch.requestPaused') void intercept(m.params).catch(async error => {
    await pause(50); // StrictMode can cancel the first mount request before CDP resumes it.
    if (String(error).includes('Invalid InterceptionId') && cancelledRequests.has(m.params.networkId)) {
      cancelledInterceptions.push({ networkId: m.params.networkId });
    } else exceptions.push({ interceptionError: String(error) });
  });
};
async function intercept({ requestId, request }) {
  const isChat = request.method === 'POST' && request.url === be + '/api/v1/chat/stream';
  const isArticle = request.method === 'GET' && request.url.startsWith(be + '/api/v1/documents/');
  if (fault && (fault.remaining > 0 || fault.target === 'article') && (fault.target === 'chat' ? isChat : isArticle)) {
    const activeFault = fault;
    if (fault.action === 'hold') { pausedRequests.push(requestId); return; }
    if (fault.action === '404') {
      await command('Fetch.fulfillRequest', { requestId, responseCode: 404,
        responseHeaders: [{ name: 'Content-Type', value: 'application/json' }, { name: 'Access-Control-Allow-Origin', value: fe }],
        body: Buffer.from(JSON.stringify({ error: { code: 'ARTICLE_NOT_FOUND', message: 'Không tìm thấy Điều luật kiểm thử.', retryable: false } })).toString('base64') });
      activeFault.remaining--;
      return;
    }
    await command('Fetch.failRequest', { requestId, errorReason: 'ConnectionReset' }); activeFault.remaining--; return;
  }
  await command('Fetch.continueRequest', { requestId });
}
async function release() {
  fault = null;
  for (const requestId of pausedRequests.splice(0)) await command('Fetch.continueRequest', { requestId }).catch(() => {});
}
async function js(expression) {
  const r = await command('Runtime.evaluate', { expression, awaitPromise: true, returnByValue: true });
  if (r.exceptionDetails) throw new Error(JSON.stringify(r.exceptionDetails));
  return r.result.value;
}
async function until(expression, timeout = 20000) {
  const end = Date.now() + timeout;
  while (Date.now() < end) { const value = await js(expression); if (value) return value; await pause(50); }
  throw new Error('UI deadline: ' + expression);
}
async function untilFn(fn, timeout = 20000) {
  const end = Date.now() + timeout;
  while (Date.now() < end) { const value = await fn(); if (value) return value; await pause(80); }
  throw new Error('Service-state deadline');
}
async function screenshot(name) {
  const r = await command('Page.captureScreenshot', { format: 'png' });
  await writeFile(path.join(out, name + '.png'), Buffer.from(r.data, 'base64'));
}
async function open(route = '/') {
  await release();
  await command('Page.navigate', { url: fe + route });
  await until("document.readyState==='complete' && (!!document.querySelector('textarea') || !!document.querySelector('[data-testid=article-content]') || !!document.querySelector('[role=status]'))");
}
async function button(label, scope = 'document') {
  const query = `[...${scope}.querySelectorAll('button')].find(b=>(b.textContent.trim()===${JSON.stringify(label)}||b.getAttribute('aria-label')===${JSON.stringify(label)})&&!b.disabled)`;
  await until(`!!(${query})`);
  await js(`(${query}).click()`);
}
async function ask(question) {
  await until("!!document.querySelector('textarea')");
  await js(`(()=>{const e=document.querySelector('textarea');Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype,'value').set.call(e,${JSON.stringify(question)});e.dispatchEvent(new Event('input',{bubbles:true}));})()`);
  await until("!document.querySelector('[data-testid=send]').disabled");
  await js("document.querySelector('[data-testid=send]').click()");
}
const routeId = () => js("location.pathname.match(/^\\/c\\/(\\d+)$/)?.[1] ?? null");
async function conversation() { return until("location.pathname.match(/^\\/c\\/(\\d+)$/)?.[1] ?? null"); }
async function rows(id) {
  const r = await fetch(be + '/api/v1/conversations/' + id + '/messages');
  assert.equal(r.status, 200); return r.json();
}
async function terminal(id, state) {
  return untilFn(async () => { const r = await rows(id); return r.at(-1)?.state === state ? r : null; });
}
async function fixtureCalls(question) {
  assert.ok(process.env.FIXTURE_LOG, 'FIXTURE_LOG required for duplicate-AI assertion');
  const raw = await readFile(process.env.FIXTURE_LOG, 'utf8').catch(() => '');
  return raw.split(/\r?\n/).filter(Boolean).map(s => JSON.parse(s)).filter(r => r.question === question);
}
async function answered(question = 'week10-answer-' + suffix + '-' + requests.length) {
  await open(); await ask(question);
  await until("!!document.querySelector('[data-testid=answer]')", mode === 'live' ? 65000 : 20000);
  const id = await conversation(), saved = await terminal(id, 'completed');
  assert.equal(saved.at(-1).answerStatus, 'answered');
  return { id, saved, question };
}
async function citation(index = 0) {
  await until(`document.querySelectorAll('[data-testid=cite-ref]').length>${index}`);
  await js(`document.querySelectorAll('[data-testid=cite-ref]')[${index}].click()`);
}
async function articleReady() { await until("!!document.querySelector('[data-testid=article-content]')"); }
const pageWidth = () => js('({viewport:innerWidth,scroll:document.documentElement.scrollWidth})');
async function assertArticle(expected = expectedArticle) {
  assert.ok(expected, 'ARTICLE_EXPECTED required');
  await articleReady();
  const got = await js("({content:document.querySelector('[data-testid=article-content]').textContent,title:document.querySelector('[data-testid=article-document]').textContent,article:document.querySelector('[data-testid=article-title]').textContent})");
  assert.equal(got.content, expected.content); assert.equal(got.title, expected.document_title); assert.equal(got.article, expected.article);
  return { contentLength: got.content.length, exactFullArticle: true };
}
async function safeLink(selector, expectedUrl) {
  const link = await js(`(()=>{const a=document.querySelector(${JSON.stringify(selector)});return a?{href:a.href,target:a.target,rel:a.rel}:null})()`);
  assert.ok(link); assert.equal(link.href, expectedUrl); assert.equal(link.target, '_blank');
  assert.ok(link.rel.split(/\s+/).includes('noopener')); assert.ok(link.rel.split(/\s+/).includes('noreferrer')); return link;
}
async function run(id, fn) {
  const started = Date.now();
  try { const detail = await fn(); results.push({ id, status: 'PASS', ms: Date.now() - started, detail }); }
  catch (error) {
    results.push({ id, status: 'FAIL', ms: Date.now() - started, error: String(error).slice(0, 1500) });
    await screenshot('failure-' + id).catch(() => {});
  } finally { await release(); }
  console.log(results.at(-1).status + ' ' + id);
}

try {
  await command('Page.enable'); await command('Runtime.enable'); await command('Network.enable');
  await command('Network.setBlockedURLs', { urls: ['*fonts.googleapis.com*', '*fonts.gstatic.com*'] });
  await command('Network.setCacheDisabled', { cacheDisabled: true });
  await command('Emulation.setDeviceMetricsOverride', { width: 1280, height: 900, deviceScaleFactor: 1, mobile: false });
  await command('Page.addScriptToEvaluateOnNewDocument', { source: `window.__week10Scrolls=[];const original=Element.prototype.scrollIntoView;Element.prototype.scrollIntoView=function(options){window.__week10Scrolls.push({testId:this.getAttribute('data-testid'),text:this.textContent,options});return original.call(this,options);};` });
  if (mode === 'mock') {
    await command('Fetch.enable', { patterns: [{ urlPattern: be + '/api/v1/*', requestStage: 'Request' }] });
    await run('S01', async () => {
      await open(); assert.equal(await js("document.querySelectorAll('[data-testid=msg-assistant]').length"), 0);
      assert.ok(await js("!!document.querySelector('textarea') && !document.querySelector('textarea').disabled && document.querySelectorAll('[data-testid=suggestion]').length>0"));
      assert.ok(await js("document.querySelector('textarea').value==='' && document.querySelector('[data-testid=send]').disabled"));
      return { emptyChat: true, inputReady: true };
    });
    await run('S02', async () => {
      await open(); const before = requests.length;
      await ask('week10-slow-answer-loading-' + suffix);
      await until("!!document.querySelector('[data-testid=msg-assistant] [role=status]')");
      assert.ok(await js("document.querySelector('[data-testid=send]').disabled"));
      await js("document.querySelector('[data-testid=send]').click()"); await pause(100);
      assert.equal(requests.length, before + 1);
      await until("!!document.querySelector('[data-testid=answer]')"); return { posts: 1, statusVisible: true };
    });
    await run('S03', async () => {
      const { saved } = await answered();
      const assistant = saved.at(-1);
      const text = await js("document.querySelector('[data-testid=answer]').textContent");
      assert.equal(text, assistant.content.replace(/\[C(\d+)\]/g, '$1'));
      assert.equal(await js("document.querySelectorAll('[data-testid=citation]').length"), assistant.citations.length);
      await screenshot('answered'); return { answerMatchesCanonicalComplete: true, citations: assistant.citations.length };
    });
    await run('S04', async () => {
      await open(); await ask('week10-insufficient-' + suffix);
      await until("!!document.querySelector('[data-testid=notice-info]')");
      assert.equal(await js("document.querySelectorAll('[data-testid=citation],[data-testid=cite-ref],[data-testid=notice-error]').length"), 0);
      const saved = await terminal(await conversation(), 'completed'); assert.equal(saved.at(-1).answerStatus, 'insufficient_context');
      return { completedInsufficient: true, citations: 0 };
    });
    await run('S05', async () => {
      await open(); const question = 'week10-retry-' + suffix;
      await ask(question); await until("!!document.querySelector('[data-testid=notice-error]')");
      const original = requests.at(-1), id = await conversation(); await terminal(id, 'failed');
      await button('Thử lại', "document.querySelector('[data-testid=notice-error]')");
      await until("!!document.querySelector('[data-testid=answer]')");
      assert.notEqual(requests.at(-1).clientRequestId, original.clientRequestId);
      const saved = await terminal(id, 'completed'); assert.equal(saved.length, 4);
      assert.equal((await fixtureCalls(question)).length, 2); return { knownFailureNewUuid: true, messages: saved.length };
    });
    await run('S06', async () => {
      await open(); await ask('week10-invalid-' + suffix); await until("!!document.querySelector('[data-testid=notice-error]')");
      assert.equal(await js("document.querySelector('[data-testid=notice-error]').querySelectorAll('button').length"), 0);
      assert.equal(await js("document.querySelectorAll('[data-testid=answer],[data-testid=citation]').length"), 0);
      const saved = await terminal(await conversation(), 'failed'); assert.equal(saved.at(-1).errorCode, 'UPSTREAM_INVALID_RESPONSE');
      return { nonRetryableFailure: true };
    });
    await run('S07', async () => {
      await open(); const question = 'week10-answer-network-' + suffix, before = requests.length;
      fault = { target: 'chat', action: 'fail', remaining: 1 }; await ask(question);
      await until("!!document.querySelector('[data-testid=notice-error]')");
      const original = requests.at(-1); assert.equal(await routeId(), null);
      assert.equal((await fixtureCalls(question)).length, 0);
      await button('Thử lại', "document.querySelector('[data-testid=notice-error]')");
      await until("!!document.querySelector('[data-testid=answer]')");
      assert.equal(requests.length, before + 2); assert.equal(requests.at(-1).clientRequestId, original.clientRequestId);
      const saved = await terminal(await conversation(), 'completed'); assert.equal(saved.length, 2);
      assert.equal((await fixtureCalls(question)).length, 1);
      await open(); const postMetaQuestion = 'week10-slow-answer-network-postmeta-' + suffix;
      await js(`(() => {
        const originalFetch = window.fetch.bind(window);
        let armed = true;
        window.fetch = async (...args) => {
          const response = await originalFetch(...args);
          if (!armed || String(args[0]) !== ${JSON.stringify(be + '/api/v1/chat/stream')}) return response;
          armed = false;
          const reader = response.body.getReader(), decoder = new TextDecoder();
          let prefix = '', receivedMeta = false;
          const body = new ReadableStream({async pull(controller) {
            if (receivedMeta) {
              controller.error(new TypeError('Controlled stream connection reset after meta'));
              void reader.cancel().catch(() => {}); return;
            }
            const item = await reader.read();
            if (item.done) { controller.close(); return; }
            prefix += decoder.decode(item.value, {stream: true});
            controller.enqueue(item.value);
            receivedMeta = /event:\\s*meta/.test(prefix) && /\\r?\\n\\r?\\n/.test(prefix);
          }});
          return new Response(body, {status: response.status, headers: response.headers});
        };
      })()`);
      await ask(postMetaQuestion); const id = await conversation(), postMetaOriginal = requests.at(-1);
      await until("!!document.querySelector('[data-testid=notice-error]')");
      await terminal(id, 'completed');
      await button('Thử lại', "document.querySelector('[data-testid=notice-error]')");
      await until("!!document.querySelector('[data-testid=answer]')");
      assert.equal(requests.at(-1).clientRequestId, postMetaOriginal.clientRequestId);
      assert.equal((await rows(id)).length, 2); assert.equal((await fixtureCalls(postMetaQuestion)).length, 1);
      return { beforeMetaDisconnect: 'CDP connection reset', afterMetaDisconnect: 'controlled reader failure after actual meta', sameUuid: true, aiCallsPerAcceptedTurn: 1 };
    });
    await run('S08', async () => {
      const outcomes = [];
      for (const variant of ['answer', 'failed', 'replay']) {
        await open(); const question = `week10-slow-${variant === 'failed' ? 'failed' : 'answer'}-stop-${variant}-${suffix}`;
        await ask(question); const id = await conversation(), original = requests.at(-1);
        await button('Dừng nhận'); await until("!!document.querySelector('[data-testid=notice-error]')");
        assert.equal(await js("[...document.querySelectorAll('button')].filter(b=>b.textContent.trim()==='Dừng nhận').length"), 0);
        if (variant === 'answer') {
          await button('Tải lại trạng thái');
          await until("!!document.querySelector('[data-testid=msg-assistant] [role=status]')");
          assert.ok(await js("document.querySelector('[data-testid=send]').disabled"));
        }
        const endState = variant === 'failed' ? 'failed' : 'completed';
        const saved = await terminal(id, endState);
        if (variant === 'replay') {
          await button('Thử lại', "document.querySelector('[data-testid=notice-error]')");
          await until("!!document.querySelector('[data-testid=answer]')");
          assert.equal(requests.at(-1).clientRequestId, original.clientRequestId);
        } else {
          await button('Tải lại trạng thái');
          await until(variant === 'failed' ? "!!document.querySelector('[data-testid=notice-error]')" : "!!document.querySelector('[data-testid=answer]')");
        }
        assert.equal(saved.length, 2); assert.equal((await fixtureCalls(question)).length, 1);
        outcomes.push({ variant, endState, messages: saved.length, aiCalls: 1 });
      }
      return { outcomes };
    });
    await run('S09', async () => {
      await open(); const question = 'week10-slow-answer-navigation-' + suffix;
      await ask(question); const id = await conversation();
      await js("document.querySelector('[data-testid=new-chat]').click()"); await until("location.pathname==='/'");
      await terminal(id, 'completed'); await pause(100);
      assert.equal(await js("document.querySelectorAll('[data-testid=msg-assistant],[data-testid=answer]').length"), 0);
      return { lateResponseDiscarded: true };
    });
    await run('S10', async () => {
      await open(); await ask('week10-slow-answer-history-' + suffix); const id = await conversation();
      await open('/c/' + id);
      await until("!!document.querySelector('[data-testid=msg-assistant] [role=status]')");
      assert.ok(await js("document.querySelector('[data-testid=send]').disabled"));
      await until("[...document.querySelectorAll('button')].some(b=>b.textContent.trim()==='Tải lại trạng thái')");
      await terminal(id, 'completed'); await button('Tải lại trạng thái');
      await until("!!document.querySelector('[data-testid=answer]')"); return { pendingHistoryBlocked: true, refreshCompleted: true };
    });
    await run('S11', async () => {
      await answered(); await citation(0); const article = await assertArticle();
      await until("!!document.querySelector('[data-testid=cited-highlight]')");
      const first = await js("document.querySelector('[data-testid=cited-highlight]').textContent"); assert.match(first, /^1\.\s/);
      assert.ok(await js("window.__week10Scrolls.some(r=>r.testId==='cited-highlight'&&r.text===document.querySelector('[data-testid=cited-highlight]').textContent)"));
      await button('Đóng'); await citation(1); await articleReady();
      const second = await js("document.querySelector('[data-testid=cited-highlight]')?.textContent"); assert.match(second, /^2\.\s/); assert.notEqual(second, first);
      const visible = await js("(()=>{const a=document.querySelector('[data-testid=cited-highlight]').getBoundingClientRect();return a.bottom>0&&a.top<innerHeight})()"); assert.ok(visible);
      await screenshot('viewer-focus');
      const sameUnitRoute = '/documents/' + expectedArticle.document_id + '?articleId=' + expectedArticle.article_id + '&clause=' + encodeURIComponent('Khoản 1');
      await open(sameUnitRoute + '&cite=C1'); await articleReady();
      await until("!!document.querySelector('[data-testid=cited-highlight]')");
      await until("window.__week10Scrolls.some(r=>r.testId==='cited-highlight')");
      const before = await js("window.__week10Scrolls.length");
      await js(`history.pushState({},'',${JSON.stringify(sameUnitRoute + '&cite=C2')});dispatchEvent(new PopStateEvent('popstate'))`);
      await until("document.querySelector('[data-testid=cited-unit]')?.textContent.includes('C2')");
      await until(`window.__week10Scrolls.length>${before}`);
      assert.match(await js("document.querySelector('[data-testid=cited-highlight]').textContent"), /^1\.\s/);
      return { ...article, focusChanged: true, scrollObserved: true, sameMountedViewerSameUnitNewCitationScroll: true };
    });
    await run('S12', async () => {
      assert.ok(expectedArticle);
      const route = '/documents/' + expectedArticle.document_id + '?articleId=' + expectedArticle.article_id + '&clause=' + encodeURIComponent('Khoản 999') + '&cite=C1';
      await open(route); const article = await assertArticle();
      assert.equal(await js("document.querySelectorAll('[data-testid=cited-highlight]').length"), 0);
      assert.equal(await js("document.querySelector('[data-testid=cited-unit]')?.getAttribute('data-located')"), 'false');
      return { ...article, missingUnitExplainedWithoutFalseHighlight: true };
    });
    await run('S13', async () => {
      await answered(); fault = { target: 'article', action: '404', remaining: 1 }; await citation();
      await until("!!document.querySelector('[data-testid=drawer] [data-testid=notice-info]')");
      const link = await safeLink('[data-testid=fallback-source-link]', expectedArticle.source_url);
      assert.equal(await js("document.querySelectorAll('[data-testid=article-content]').length"), 0);
      assert.equal(await js("document.querySelectorAll('[data-testid=answer]').length"), 1); return { citation404Fallback: true, ...link };
    });
    await run('S14', async () => {
      await answered(); await citation(); await articleReady();
      return safeLink('[data-testid=source-link]', expectedArticle.source_url);
    });
    await run('S15', async () => {
      const metrics = [];
      for (const width of [360, 768, 1280]) {
        await command('Emulation.setDeviceMetricsOverride', { width, height: 900, deviceScaleFactor: 1, mobile: false });
        await answered('week10-answer-responsive-' + width + '-' + suffix);
        const chat = await pageWidth(); assert.ok(chat.scroll <= width + 1, JSON.stringify(chat));
        assert.ok(await js("(()=>{const e=document.querySelector('textarea').getBoundingClientRect();const b=document.querySelector('[data-testid=send]').getBoundingClientRect();return e.width>0&&e.left>=0&&e.right<=innerWidth+1&&b.width>0&&b.left>=0&&b.right<=innerWidth+1})()"));
        assert.ok(await js("[...document.querySelectorAll('[data-testid=citation],[data-testid=cite-ref]')].every(e=>{const r=e.getBoundingClientRect();return r.width>0&&r.left>=-1&&r.right<=innerWidth+1})"));
        await citation(); await articleReady(); const viewer = await pageWidth(); assert.ok(viewer.scroll <= width + 1, JSON.stringify(viewer));
        await screenshot('responsive-' + width);
        await button('Đóng');
        await ask('week10-slow-answer-responsive-stop-' + width + '-' + suffix);
        const id = await conversation();
        await until("[...document.querySelectorAll('button')].some(b=>b.textContent.trim()==='Dừng nhận')");
        const stopFits = await js("(()=>{const e=[...document.querySelectorAll('button')].find(b=>b.textContent.trim()==='Dừng nhận').getBoundingClientRect();return e.width>0&&e.left>=0&&e.right<=innerWidth+1})()");
        assert.ok(stopFits); await button('Dừng nhận');
        await until("!!document.querySelector('[data-testid=notice-error] button')");
        const retryFits = await js("(()=>{const e=document.querySelector('[data-testid=notice-error] button').getBoundingClientRect();return e.width>0&&e.left>=0&&e.right<=innerWidth+1})()");
        assert.ok(retryFits); await terminal(id, 'completed');
        metrics.push({ width, chat, viewer, stopFits, retryFits });
      }
      await command('Emulation.setDeviceMetricsOverride', { width: 1280, height: 900, deviceScaleFactor: 1, mobile: false });
      return { metrics };
    });
    await run('S16', async () => {
      const originalRoute = '/documents/' + expectedArticle.document_id + '?articleId=' + expectedArticle.article_id;
      await open(originalRoute); await assertArticle();
      const otherRoute = '/documents/' + expectedArticle.document_id + '?articleId=dieu-74';
      fault = { target: 'article', action: 'hold', remaining: 1 };
      await js(`history.pushState({},'',${JSON.stringify(otherRoute)});dispatchEvent(new PopStateEvent('popstate'))`);
      await until("!!document.querySelector('[role=status]')");
      assert.equal(await js("document.querySelectorAll('[data-testid=article-content]').length"), 0);
      await release(); await articleReady();
      const actual = await (await fetch(be + '/api/v1/documents/' + expectedArticle.document_id + '?articleId=dieu-74')).json();
      assert.equal(await js("document.querySelector('[data-testid=article-content]').textContent"), actual.content);
      assert.notEqual(actual.content, expectedArticle.content);
      return { loadingVisible: true, staleContentHidden: true, changedSelectionFullText: true };
    });
    await run('S17', async () => {
      await answered(); const before = requests.length;
      fault = { target: 'article', action: 'fail', remaining: 1 }; await citation();
      await until("!!document.querySelector('[data-testid=drawer] [data-testid=notice-error]')");
      assert.ok(await js("[...document.querySelector('[data-testid=drawer]').querySelectorAll('button')].some(b=>b.textContent.trim()==='Thử lại')"));
      assert.equal(await js("document.querySelectorAll('[data-testid=article-content]').length"), 0);
      assert.equal(await js("document.querySelectorAll('[data-testid=answer]').length"), 1); assert.equal(requests.length, before);
      return { articleErrorIsolated: true, chatIntact: true };
    });
    await run('S18', async () => {
      await answered(); const before = requests.length, articleBefore = articleRequestDetails.length;
      fault = { target: 'article', action: 'fail', remaining: 1 }; await citation(1);
      await until("!!document.querySelector('[data-testid=drawer] [data-testid=notice-error]')");
      await release();
      await button('Thử lại', "document.querySelector('[data-testid=drawer]')"); await assertArticle();
      assert.equal(requests.length, before);
      const attempted = articleRequestDetails.slice(articleBefore).filter(r => !cancelledRequests.has(r.id));
      assert.equal(attempted.length, 2); assert.equal(attempted[0].url, attempted[1].url);
      assert.match(await js("document.querySelector('[data-testid=cited-highlight]').textContent"), /^2\.\s/);
      return { retriedSameArticle: true, newChatRequests: 0, articleAttempts: attempted.length };
    });
  } else if (mode === 'corpus') {
    assert.ok(expectedArticle, 'ARTICLE_EXPECTED required');
    const route = '/documents/' + expectedArticle.document_id + '?articleId=' + expectedArticle.article_id;
    await run('CORPUS_ARTICLE', async () => { await open(route); return assertArticle(); });
    await run('CORPUS_FOCUS', async () => {
      await open(route + '&clause=' + encodeURIComponent('Khoản 2') + '&cite=C1'); await articleReady();
      assert.match(await js("document.querySelector('[data-testid=cited-highlight]')?.textContent"), /^2\.\s/);
      assert.ok(await js("window.__week10Scrolls.some(r=>r.testId==='cited-highlight')"));
      return { realArticleFocus: true };
    });
    await run('CORPUS_SOURCE', async () => safeLink('[data-testid=source-link]', expectedArticle.source_url));
  } else {
    assert.ok(process.env.LIVE_QUESTIONS, 'LIVE_QUESTIONS JSON file required');
    const questions = JSON.parse(await readFile(process.env.LIVE_QUESTIONS, 'utf8'));
    assert.ok(questions.answered && questions.insufficient_context);
    await run('LIVE_ANSWERED', async () => {
      const { id, saved } = await answered(questions.answered); await citation(); await articleReady();
      const citationData = saved.at(-1).citations[0];
      const r = await fetch(be + '/api/v1/documents/' + encodeURIComponent(citationData.documentId) + '?articleId=' + encodeURIComponent(citationData.articleId));
      assert.ok(r.ok); const actual = await r.json();
      assert.equal(await js("document.querySelector('[data-testid=article-content]').textContent"), actual.content);
      await safeLink('[data-testid=source-link]', actual.sourceUrl);
      await screenshot('live-answer-viewer'); await writeFile(path.join(out, 'live-answered.json'), JSON.stringify(saved, null, 2));
      return { conversationId: id, status: 'answered', citationCount: saved.at(-1).citations.length, fullArticleMatchesBackend: true };
    });
    await run('LIVE_INSUFFICIENT', async () => {
      await open(); await ask(questions.insufficient_context); await until("!!document.querySelector('[data-testid=notice-info],[data-testid=notice-error]')", 65000);
      assert.equal(await js("document.querySelectorAll('[data-testid=notice-error],[data-testid=cite-ref]').length"), 0);
      const id = await conversation(), saved = await terminal(id, 'completed'); assert.equal(saved.at(-1).answerStatus, 'insufficient_context');
      await screenshot('live-insufficient'); await writeFile(path.join(out, 'live-insufficient.json'), JSON.stringify(saved, null, 2));
      return { conversationId: id, status: 'insufficient_context' };
    });
  }
} catch (error) {
  console.error('Probe setup failure:', error.name);
  results.push({ id: 'SETUP', status: 'FAIL', error: String(error).slice(0, 1500) });
} finally {
  for (const id of expectedIds) if (!results.some(r => r.id === id)) results.push({ id, status: 'NOT_RUN', reason: 'Probe did not reach this mandatory case' });
  const passed = results.filter(r => expectedIds.includes(r.id) && r.status === 'PASS').length;
  const status = passed === expectedIds.length && results.every(r => r.status === 'PASS') && !exceptions.length ? 'PASS' : 'FAIL';
  await writeFile(path.join(out, 'ui-results.json'), JSON.stringify({ mode, status, expectedIds, expected_ids: expectedIds, total: expectedIds.length,
    passed, skipped: results.filter(r => r.status === 'NOT_RUN').length, results, exceptions,
    queryTransport: mode === 'mock' ? 'real UI/Java/PostgreSQL; labelled Team3 fixture via Team2 adapter; controlled browser faults' : 'real UI/Java/Team2 service; no browser payload interception',
    articleSource: 'Article Store; API-fault fixtures only in mock mode', modelInference: mode === 'live' ? 'real configured pipeline; no forced outcome' : false }, null, 2));
  await release().catch(() => {}); await command('Page.close').catch(() => {}); ws.close();
  if (status !== 'PASS') process.exitCode = 1;
  console.log(JSON.stringify({ mode, status, passed, total: expectedIds.length }));
}
