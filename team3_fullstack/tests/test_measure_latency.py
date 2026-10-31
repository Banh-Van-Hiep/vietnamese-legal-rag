import copy
import json
from pathlib import Path
import tempfile
import time
import uuid
import unittest
from unittest.mock import patch

from team3_fullstack.tools import measure_latency as runner
from team3_fullstack.tools.latency_report import PublicContract

ROOT = Path(__file__).resolve().parents[2]
EXAMPLES = json.loads((ROOT/'contracts/v0.1/public_examples.json').read_text(encoding='utf-8'))


class Response:
    def __init__(self, data=None, chunks=None, status=200, headers=None):
        self.data=data; self.chunks=chunks; self.status_code=status; self.headers=headers or {}; self.closed=False; self.failed=False
    def __enter__(self): return self
    def __exit__(self, *args): return False
    def close(self): self.closed=True
    def success(self): pass
    def failure(self, message): self.failed=True
    def iter_content(self, **kwargs):
        return iter(self.chunks) if self.chunks is not None else iter([json.dumps(self.data).encode()])


class Client:
    def __init__(self, *, insufficient=False, heartbeat=False, bad_article=False, status=200):
        self.insufficient=insufficient; self.heartbeat=heartbeat; self.bad_article=bad_article; self.status=status; self.posts=[]; self.gets=[]; self.responses=[]
    def post(self, path, **kwargs):
        self.posts.append(kwargs)
        payload=json.loads(kwargs['data'].decode('utf-8'))
        result=copy.deepcopy(EXAMPLES['InsufficientComplete'] if self.insufficient else EXAMPLES['Complete'])
        result['clientRequestId']=payload['clientRequestId']
        meta={k:result[k] for k in ('conversationId','clientRequestId','userMessageId','assistantMessageId','createdAt')}
        frames=[('meta',meta)]
        if not self.insufficient: frames.append(('delta',{'text':result['answer']}))
        frames.append(('complete',result))
        raw=''.join('event: '+k+'\ndata: '+json.dumps(v,ensure_ascii=False)+'\n\n' for k,v in frames).encode()
        if self.heartbeat:
            def forever():
                import gevent
                while True:
                    gevent.sleep(.005); yield b': heartbeat\n\n'
            chunks=forever()
        else: chunks=[raw]
        res=Response(chunks=chunks,status=self.status,headers={'X-Request-ID':str(uuid.uuid4())})
        self.responses.append(res); return res
    def get(self, path, **kwargs):
        self.gets.append(path)
        from urllib.parse import unquote,parse_qs,urlsplit
        parsed=urlsplit(path);doc=unquote(parsed.path.rsplit('/',1)[-1]);art=parse_qs(parsed.query)['articleId'][0]
        res=Response(data={'documentId':'wrong' if self.bad_article else doc,'documentTitle':'Fixture','articleId':art,'article':'Điều 1','content':'Nguyên văn kiểm thử','sourceUrl':'https://example.com/mock'},headers={'X-Request-ID':str(uuid.uuid4())})
        self.responses.append(res); return res


class RunnerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.contract=PublicContract(ROOT)

    def sample(self, client, warmup=False, timeout=.5):
        return runner.request_sample(client, {'id':'sample','question':'Câu hỏi'}, self.contract, timeout, warmup)

    def test_measures_terminal_and_article_with_new_uuid_every_attempt(self):
        client=Client();one=self.sample(client);two=self.sample(client)
        self.assertEqual(one['outcome'],'completed');self.assertEqual(one['article']['outcome'],'completed')
        self.assertNotEqual(one['client_request_id'],two['client_request_id'])
        self.assertNotEqual(one['trace_id'],two['trace_id'])
        self.assertNotIn('X-Request-ID',client.posts[0]['headers'])
        self.assertEqual(set(json.loads(client.posts[0]['data'])),{'question','clientRequestId'})
        self.assertIn('Câu hỏi',client.posts[0]['data'].decode('utf-8'))
        self.assertNotIn('answer',one);self.assertNotIn('question',one)
        self.assertTrue(all(r.closed for r in client.responses))

    def test_astral_question_uses_utf8_bytes_within_backend_body_limit(self):
        client=Client()
        row=runner.request_sample(client,{'id':'emoji','question':'😀'*2000},self.contract,.5)
        self.assertEqual(row['outcome'],'completed')
        self.assertLess(len(client.posts[0]['data']),16*1024)

    def test_insufficient_does_not_invent_lookup(self):
        client=Client(insufficient=True);row=self.sample(client)
        self.assertEqual(row['answer_status'],'insufficient_context');self.assertIsNone(row['article']);self.assertEqual(client.gets,[])

    def test_heartbeat_cannot_extend_total_deadline(self):
        client=Client(heartbeat=True);start=time.perf_counter();row=self.sample(client,timeout=.04)
        self.assertEqual(row['error_code'],'REQUEST_DEADLINE');self.assertLess(time.perf_counter()-start,1)
        self.assertTrue(client.responses[0].closed)

    def test_http_failure_is_retained_without_reading_private_error_body(self):
        row=self.sample(Client(status=503))
        self.assertEqual(row['outcome'],'failed');self.assertEqual(row['error_code'],'HTTP_503')
        self.assertGreaterEqual(row['elapsed_ms'],0)

    def test_bad_article_does_not_erase_successful_chat(self):
        row=self.sample(Client(bad_article=True))
        self.assertEqual(row['outcome'],'completed');self.assertEqual(row['article']['outcome'],'failed')
        self.assertEqual(row['article']['error_code'],'INVALID_ARTICLE_RESPONSE')

    def test_warmup_errors_counts_and_missing_timing_are_separate(self):
        client=Client();warm=self.sample(client,True);ok=self.sample(client);bad=self.sample(Client(status=503))
        result=runner.summarize([warm,ok,bad],{},'mock')
        self.assertEqual(result['total_requests'],2);self.assertEqual(result['successful_requests'],1);self.assertEqual(result['failed_requests'],1)
        self.assertEqual(result['latency_distribution_seconds']['samples'],1)
        self.assertEqual(result['warmup']['total_requests'],1);self.assertFalse(result['live_target_verified'])
        self.assertEqual(result['timing_coverage']['matched_successful'],0)

    def test_replay_duplicate_origin_and_unmatched_request_are_not_live_timings(self):
        row=self.sample(Client());trace=row['trace_id']
        good={'trace_id':trace,'client_request_id':row['client_request_id'],'outcome':'completed','upstream_origin':'http://localhost:8001','transport_connected':True,'total_ms':5,'phases_ms':dict.fromkeys(runner.PHASES,1.)}
        for change in [{'outcome':'replayed'},{'client_request_id':'wrong'},{'error':'DUPLICATE_TIMING'},{'upstream_origin':'http://localhost:9999'}]:
            result=runner.summarize([copy.deepcopy(row)],{trace:{**good,**change}},'live','http://localhost:8001',True)
            self.assertFalse(result['live_target_verified']);self.assertEqual(result['timing_coverage']['matched_successful'],0)
        result=runner.summarize([copy.deepcopy(row)],{trace:good},'live','http://localhost:8001',True)
        self.assertTrue(result['live_target_verified']);self.assertFalse(result['viewer_ui_verified'])
        closed=runner.summarize([copy.deepcopy(row)],{trace:{**good,'transport_connected':False}},'live','http://localhost:8001',True)
        self.assertTrue(closed['live_target_verified'])

    def test_existing_output_prevents_any_requests(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'report.json';path.write_text('keep',encoding='utf-8')
            with patch.object(runner,'run_jobs',side_effect=AssertionError('must not send')):
                code=runner.main(['--mode','mock','--dataset','missing.json','--output',str(path)])
            self.assertEqual(code,2);self.assertEqual(path.read_text(),'keep')

    def test_failure_timing_is_kept_as_diagnostic_without_entering_success_percentiles(self):
        row=self.sample(Client(status=503));trace=row['trace_id']
        timing={'trace_id':trace,'client_request_id':row['client_request_id'],'outcome':'failed',
                'upstream_origin':'http://localhost:8001','transport_connected':True,'total_ms':5,
                'phases_ms':{'backend_init':1.,'ai_service':2.,'db_persist':None,'stream_finish':1.}}
        report=runner.summarize([row],{trace:timing},'mock')
        self.assertEqual(report['timing_coverage']['matched_failed'],1)
        self.assertIsNone(report['samples'][0]['backend_timing']['phases_ms']['db_persist'])
        self.assertIsNone(report['phases_breakdown_p95_seconds']['ai_service'])

    def test_live_preflight_refuses_mock_and_unready_even_with_matching_dev_proof(self):
        import argparse
        import hashlib
        from team3_fullstack.tools.latency_report import BenchmarkError
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'dev.json';proof_path=Path(tmp)/'split.json'
            rows=[{'id':str(i),'question':'Câu hỏi '+str(i),'expected_status':'answered','ground_truth':'Đáp án',
                   'gold_chunk_ids':['chunk'],'citation':'Điều 1','category':'Fixture','author':'Nhóm kiểm thử'} for i in range(90)]
            path.write_text(json.dumps(rows,ensure_ascii=False),encoding='utf-8')
            proof={'format_version':1,'status':'split_only','input':{'count':150},'outputs':{
                'dev':{'count':90,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'status_counts':{'answered':90,'insufficient_context':0}},'test':{'count':60}}}
            proof_path.write_text(json.dumps(proof),encoding='utf-8')
            args=argparse.Namespace(dataset=path,split_report=proof_path,timing_log=Path(tmp)/'backend.log',rag_url='http://localhost:8001')
            for status,mode in [(503,''),(200,'mock')]:
                response=Response(status=status,headers={'X-RAG-MODE':mode});response.content=b'{"status":"ready"}'
                with patch('requests.get',return_value=response), self.assertRaises(BenchmarkError) as ctx:
                    runner.preflight_live(args,rows)
                self.assertEqual(ctx.exception.code,'RAG_NOT_READY_OR_MOCK')


if __name__ == '__main__': unittest.main()
