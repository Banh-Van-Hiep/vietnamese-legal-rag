/** Five real Backend conversations x10 turns. The RAG service is a labelled fixture. */
import assert from 'node:assert/strict';
import { randomUUID } from 'node:crypto';
import { writeFile } from 'node:fs/promises';
import path from 'node:path';
const { BE_URL: be, EVIDENCE_DIR: out } = process.env;
const samples = [], sessions = [];
let active = 0, peakInFlight = 0;
await Promise.all(Array.from({ length: 5 }, async (_, session) => {
  let conversationId;
  for (let turn = 0; turn < 10; turn++) {
    const clientRequestId = randomUUID(), started = performance.now();
    active++; peakInFlight = Math.max(peakInFlight, active);
    try {
      const response = await fetch(be + '/api/v1/chat/stream', { method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question: `fixture-load-${session}-${turn}`, clientRequestId, ...(conversationId ? { conversationId } : {}) }), signal: AbortSignal.timeout(60000) });
      const wire = await response.text(); assert.equal(response.status, 200); assert.doesNotMatch(wire, /event:\s*error/);
      const frame = wire.replaceAll('\r\n', '\n').split('\n\n').find(x => /^event:\s*complete$/m.test(x));
      assert.ok(frame); const value = JSON.parse(frame.split('\n').find(x => x.startsWith('data:')).slice(5));
      assert.equal(value.clientRequestId, clientRequestId); assert.equal(value.status, 'answered');
      assert.equal(value.citations.length, 1); if (conversationId) assert.equal(value.conversationId, conversationId);
      conversationId = value.conversationId;
      samples.push({ session, turn, clientRequestId, conversationId, elapsedMs: performance.now() - started, status: 'PASS' });
    } catch (error) { samples.push({ session, turn, status: 'FAIL', error: String(error) }); }
    finally { active--; }
  }
  if (conversationId) {
    const rows = await (await fetch(be + '/api/v1/conversations/' + conversationId + '/messages')).json();
    assert.equal(rows.length, 20); assert.ok(rows.every(m => m.state === 'completed'));
    sessions.push({ conversationId, messages: rows.length, pending: rows.filter(m => m.state === 'pending').length });
  }
}));
const report = { mode: 'Java/PostgreSQL/HTTP fixture; no model', users: 5, turnsPerSession: 10, peakInFlight,
  successfulRequests: samples.filter(s => s.status === 'PASS').length, totalRequests: samples.length, sessions, samples };
await writeFile(path.join(out, 'concurrency.json'), JSON.stringify(report, null, 2));
assert.equal(peakInFlight, 5); assert.equal(report.successfulRequests, 50); assert.equal(new Set(sessions.map(s => s.conversationId)).size, 5);
console.log(JSON.stringify({ success: report.successfulRequests, total: samples.length, peakInFlight }));
