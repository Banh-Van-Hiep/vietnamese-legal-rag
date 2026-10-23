/** Browser integration via installed Edge/Chrome DevTools; no framework dependency.
 * Prerequisites/run commands and fixture limits are in the VLRA42 quickstart. */
import assert from "node:assert/strict";
import { mkdir, writeFile } from "node:fs/promises";
import path from "node:path";
const frontend=process.env.FE_URL??"http://127.0.0.1:15173";
const backend=process.env.BE_URL??"http://127.0.0.1:18043";
const stub=process.env.STUB_URL??"http://127.0.0.1:18042";
const cdp=process.env.CDP_URL??"http://127.0.0.1:19242";
const out=process.env.EVIDENCE_DIR??"../backend/target/vlra42-browser";
await mkdir(out,{recursive:true});
const target=await (await fetch(`${cdp}/json/new?about:blank`,{method:"PUT"})).json();
const ws=new WebSocket(target.webSocketDebuggerUrl);
await new Promise((resolve,reject)=>{ws.onopen=resolve;ws.onerror=reject;});
let sequence=0, failNext=false;
const pending=new Map(), requests=[], exceptions=[], results=[];
function command(method,params={}) {
  const id=++sequence;
  return new Promise((resolve,reject)=>{
    const timer=setTimeout(()=>{pending.delete(id);reject(new Error(`CDP timeout ${method}`));},15000);
    pending.set(id,{resolve,reject,timer});ws.send(JSON.stringify({id,method,params}));
  });
}
ws.onmessage=async ({data})=>{
  const m=JSON.parse(data);
  if(m.id) { const p=pending.get(m.id);if(!p)return;pending.delete(m.id);clearTimeout(p.timer);m.error?p.reject(new Error(JSON.stringify(m.error))):p.resolve(m.result);return; }
  if(m.method==="Runtime.exceptionThrown") exceptions.push(m.params.exceptionDetails);
  if(m.method==="Network.requestWillBeSent" && m.params.request.method==="POST" && m.params.request.url===`${backend}/api/v1/chat/stream`) {
    requests.push({body:JSON.parse(m.params.request.postData),url:m.params.request.url});
  }
  if(m.method==="Fetch.requestPaused") {
    if(failNext) {failNext=false;await command("Fetch.failRequest",{requestId:m.params.requestId,errorReason:"Failed"});await command("Fetch.disable");}
    else await command("Fetch.continueRequest",{requestId:m.params.requestId});
  }
};
async function evaluate(expression) {
  const r=await command("Runtime.evaluate",{expression,awaitPromise:true,returnByValue:true});
  if(r.exceptionDetails) throw new Error(JSON.stringify(r.exceptionDetails));return r.result.value;
}
const pause=(ms)=>new Promise((r)=>setTimeout(r,ms));
async function until(expression,timeout=10000) {
  const end=Date.now()+timeout;
  while(Date.now()<end) { const value=await evaluate(expression);if(value)return value;await pause(80); }
  throw new Error(`Browser condition timed out: ${expression}\n${await evaluate("document.body.innerText")}`);
}
async function navigate(route="/") {
  await command("Page.navigate",{url:frontend+route});
  await until("document.readyState==='complete' && !!document.querySelector('textarea')");
  await pause(100);
}
async function ask(q) {
  await until("!!document.querySelector('textarea')");
  await evaluate(`(()=>{const e=document.querySelector('textarea');Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype,'value').set.call(e,${JSON.stringify(q)});e.dispatchEvent(new Event('input',{bubbles:true}));})()`);
  await until("!document.querySelector('[data-testid=send]').disabled");
  await evaluate("document.querySelector('[data-testid=send]').click()");
}
async function click(label) {
  await until(`Array.from(document.querySelectorAll('button')).some(b=>b.textContent.trim()===${JSON.stringify(label)}&&!b.disabled)`);
  await evaluate(`Array.from(document.querySelectorAll('button')).find(b=>b.textContent.trim()===${JSON.stringify(label)}&&!b.disabled).click()`);
}
async function answered(q) { await until(`Array.from(document.querySelectorAll('[data-testid=answer]')).some(e=>e.textContent.includes(${JSON.stringify(q)}))`); }
async function calls(q) {return (await (await fetch(`${stub}/__test/state`)).json()).calls.filter((c)=>c.question===q);}
async function messages(id) {const r=await fetch(`${backend}/api/v1/conversations/${id}/messages`);assert.equal(r.status,200);return r.json();}
async function caseRun(name,body) {await body();results.push({name,status:"PASS"});console.log(`PASS ${name}`);}
const suffix=Date.now().toString(36);let firstConv;
try {
  await command("Page.enable");await command("Runtime.enable");await command("Network.enable");
  await caseRun("answered + follow-up/history + original source",async()=>{
    await navigate();const q=`Answered smoke ${suffix}`;await ask(q);await answered(q);
    firstConv=await evaluate("location.pathname.split('/').pop()");assert.match(firstConv,/^[1-9][0-9]*$/);
    await until(`document.querySelector('h1')?.textContent===${JSON.stringify(q)}`);
    await until(`Array.from(document.querySelectorAll('aside a')).some(a=>a.getAttribute('href')==='/c/'+${JSON.stringify(firstConv)}&&a.textContent.includes(${JSON.stringify(q)}))`);
    assert.equal((await calls(q)).length,1);assert.equal((await calls(q))[0].history.length,0);
    assert.equal(await evaluate("!!document.querySelector('[data-testid=mock-badge]')"),true);
    await evaluate("document.querySelector('[data-testid=cite-ref]').click()");
    await until("!!document.querySelector('[data-testid=article-content]')");
    assert.match(await evaluate("document.querySelector('[data-testid=article-content]').textContent"),/Nguyên văn đầy đủ/);
    await evaluate("document.querySelector('button[aria-label=Đóng]').click()");
    const q2=`Follow-up smoke ${suffix}`;await ask(q2);await answered(q2);assert.equal((await calls(q2))[0].history.length,2);
    assert.equal(await evaluate("document.querySelector('h1').textContent"),q);
  });
  await caseRun("reload history without calling RAG again",async()=>{
    const before=(await (await fetch(`${stub}/__test/state`)).json()).calls.length;
    await navigate(`/c/${firstConv}`);await answered(`Follow-up smoke ${suffix}`);
    await until(`document.querySelector('h1')?.textContent===${JSON.stringify(`Answered smoke ${suffix}`)}`);
    assert.equal((await (await fetch(`${stub}/__test/state`)).json()).calls.length,before);
  });
  await caseRun("insufficient context is separate from service errors",async()=>{
    await navigate();await ask(`Insufficient smoke ${suffix}`);await until("document.querySelector('[data-testid=notice-info]')?.textContent.includes('Chưa đủ căn cứ')");
    assert.equal(await evaluate("document.querySelectorAll('[data-testid=cite-ref]').length"),0);
  });
  await caseRun("known failure retries with a new UUID",async()=>{
    await navigate();const q=`Known failure smoke ${suffix}`;await ask(q);await until("document.querySelector('[data-testid=notice-error]')?.textContent.includes('SERVICE_UNAVAILABLE')");
    await click("Thử lại");await answered(q);
    const attempts=requests.filter((r)=>r.body.question===q);assert.equal(attempts.length,2);assert.notEqual(attempts[0].body.clientRequestId,attempts[1].body.clientRequestId);
    assert.equal((await calls(q)).length,2);
  });
  await caseRun("stop receiving + replay retains UUID and one stored pair",async()=>{
    await navigate();const q=`Slow smoke ${suffix}`;await ask(q);await until("location.pathname.startsWith('/c/')");
    const conv=await evaluate("location.pathname.split('/').pop()");await click("Dừng nhận");
    await until("document.querySelector('[data-testid=notice-error]')?.textContent.includes('RECEIVING_STOPPED')");
    await pause(2000);await click("Thử lại");await answered(q);
    const attempts=requests.filter((r)=>r.body.question===q);assert.equal(attempts.length,2);assert.equal(attempts[0].body.clientRequestId,attempts[1].body.clientRequestId);
    assert.equal((await calls(q)).length,1);assert.equal((await messages(conv)).length,2);
    assert.equal(await evaluate("document.querySelectorAll('[data-testid=answer]').length"),1);
  });
  await caseRun("network failure before meta survives reload and keeps UUID",async()=>{
    await navigate();const q=`Network smoke ${suffix}`;failNext=true;await command("Fetch.enable",{patterns:[{urlPattern:`${backend}/api/v1/chat/stream`,requestStage:"Request"}]});
    await ask(q);await until("!!document.querySelector('[data-testid=notice-error]')");assert.equal(await evaluate("location.pathname"),"/");
    await navigate();await until("document.body.textContent.includes('Chưa rõ kết quả lượt trước')");await click("Thử lại");await answered(q);
    const attempts=requests.filter((r)=>r.body.question===q);assert.equal(attempts.length,2);assert.equal(attempts[0].body.clientRequestId,attempts[1].body.clientRequestId);
    assert.equal((await calls(q)).length,1);
  });
  await caseRun("reload while pending blocks new send then reconciles history",async()=>{
    await navigate();const q=`Reload pending smoke ${suffix}`;await ask(q);await until("location.pathname.startsWith('/c/')");
    const route=await evaluate("location.pathname");await navigate(route);
    await until("document.body.textContent.includes('Tải lại trạng thái')");assert.equal(await evaluate("document.querySelector('[data-testid=send]').disabled"),true);
    await pause(2000);await click("Tải lại trạng thái");await answered(q);assert.equal((await calls(q)).length,1);
  });
  await caseRun("switch conversation drops stale stream output",async()=>{
    await navigate();const q=`Switch pending smoke ${suffix}`;await ask(q);await until("location.pathname.startsWith('/c/')");
    // Navigate within the SPA so the same hook instance must reject late results.
    await evaluate(`document.querySelector('a[href="/c/${firstConv}"]').click()`);await answered(`Follow-up smoke ${suffix}`);await pause(2000);
    assert.equal(await evaluate(`Array.from(document.querySelectorAll('[data-testid=answer]')).some(e=>e.textContent.includes(${JSON.stringify(q)}))`),false);
  });
  await caseRun("source404 does not remove answer",async()=>{
    await navigate();const q=`Missing source smoke ${suffix}`;await ask(q);await answered(q);
    await evaluate("document.querySelector('[data-testid=cite-ref]').click()");await until("document.querySelector('[data-testid=drawer]')?.textContent.includes('Không tìm thấy điều luật')");
    await answered(q);
  });
  await caseRun("CORS allowlist works in browser and rejects other origin",async()=>{
    const r=await fetch(`${backend}/api/v1/chat/stream`,{method:"OPTIONS",headers:{Origin:frontend,"Access-Control-Request-Method":"POST","Access-Control-Request-Headers":"content-type,accept"}});
    assert.equal(r.status,200);assert.equal(r.headers.get("access-control-allow-origin"),frontend);
    const bad=await fetch(`${backend}/api/v1/health`,{headers:{Origin:"https://denied.example"}});assert.equal(bad.status,403);assert.equal(bad.headers.get("access-control-allow-origin"),null);
  });
  await caseRun("canonical Viewer deep link and reload",async()=>{
    await command("Page.navigate",{url:`${frontend}/documents/mock_v1?articleId=art1`});
    await until("!!document.querySelector('[data-testid=article-content]')");
    await command("Page.reload");await until("!!document.querySelector('[data-testid=article-content]')");
    assert.match(await evaluate("document.querySelector('[data-testid=article-content]').textContent"),/Nguyên văn đầy đủ/);
  });
  assert.equal(exceptions.length,0,JSON.stringify(exceptions));
  for(const r of requests) {assert.match(r.body.clientRequestId,/^[\da-f]{8}-[\da-f]{4}-4[\da-f]{3}-[89ab][\da-f]{3}-[\da-f]{12}$/i);assert.ok(!("history"in r.body)&&!("scenario"in r.body));if(r.body.conversationId!=null)assert.equal(typeof r.body.conversationId,"number");}
  const screenshot=await command("Page.captureScreenshot",{format:"png"});await writeFile(path.join(out,"browser.png"),Buffer.from(screenshot.data,"base64"));
} catch(error) {results.push({name:"execution",status:"FAIL",message:String(error)});throw error;}
finally {
  await writeFile(path.join(out,"results.json"),JSON.stringify({profile:"rag",rag:"HTTP test fixture only; not live",frontend,backend,results,requests,exceptions},null,2));
  await command("Page.close").catch(()=>{});ws.close();
}
