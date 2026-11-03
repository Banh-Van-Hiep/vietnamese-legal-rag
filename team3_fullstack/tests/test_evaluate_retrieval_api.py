from contextlib import contextmanager
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock,patch

from team3_fullstack.tools.evaluate_retrieval_api import evaluate
from team3_fullstack.tools.latency_report import BenchmarkError,PublicContract
from team3_fullstack.tools.measure_latency import request_sample
from team3_fullstack.tools.retrieval_api_evaluation import ManagedGateway,probe_ready
from team3_fullstack.tests.test_measure_latency import Client,ROOT


class MatrixExecutionTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name);self.calls=[];self.gateway_calls=[]
        self.matrix=self.root/'matrix.json';self.data=self.root/'queries.json'
        self.matrix.write_text(json.dumps({'format_version':1,'selected':'v2','targets':[
            {'name':'v2','rag_url':'http://127.0.0.1:8001'},
            {'name':'baseline','rag_url':'http://127.0.0.1:8002'}]}),encoding='utf-8')
        self.data.write_text(json.dumps([{'id':'q1','question':'Câu hỏi 1'},{'id':'q2','question':'Câu hỏi 2'}],ensure_ascii=False),encoding='utf-8')

    @contextmanager
    def gateway(self,target,*_):
        self.gateway_calls.append(target['rag_url'])
        yield 'http://127.0.0.1:'+('8081' if target['name']=='v2' else '8082')

    def jobs(self,rows,url,users,timeout,contract,**options):
        self.calls.append({'ids':[r['id'] for r in rows],'url':url,'users':users,'timeout':timeout,**options})
        return [{'sample_id':r['id'],'outcome':'completed','attempted':True,'elapsed_ms':10,'article':None,
                 'complete_response':{'status':'insufficient_context','answer':'Chưa đủ căn cứ.','citations':[]}} for r in rows]

    def run_matrix(self,**kwargs):
        options={'jobs':self.jobs,'gateway':self.gateway,'readiness':lambda *_:{'observed_mock_header':True}}
        options.update(kwargs)
        return evaluate(self.matrix,self.data,self.root/'output',mode='mock',**options)

    def test_same_queries_options_and_full_responses_for_all_configurations(self):
        r=self.run_matrix(warmup=1,users=1,timeout=7)
        self.assertEqual(r['status'],'COLLECTED')
        self.assertEqual([c['ids'] for c in self.calls],[['q1'],['q1','q2'],['q1'],['q1','q2']])
        self.assertTrue(all(c['capture_response'] and c['users']==1 and c['timeout']==7 for c in self.calls))
        self.assertEqual(len(r['comparison']),2)
        self.assertFalse(r['model_inference_verified'])
        self.assertTrue((self.root/'output/report.json').is_file())
        self.assertTrue((self.root/'output/comparison.md').is_file())

    def test_selected_only_routes_one_target(self):
        r=self.run_matrix(selected_only=True,warmup=0)
        self.assertEqual([x['name'] for x in r['targets']],['v2'])
        self.assertEqual(self.gateway_calls,['http://127.0.0.1:8001'])

    def test_one_unready_target_does_not_drop_other_target(self):
        def ready(url,*_):
            if url.endswith('8001'):raise BenchmarkError('RAG_NOT_READY')
            return {'observed_mock_header':True}
        r=self.run_matrix(readiness=ready,warmup=0)
        self.assertEqual(r['status'],'INCOMPLETE')
        self.assertEqual(r['targets'][0]['attempted_requests'],0)
        self.assertEqual(r['targets'][0]['failed_requests'],2)
        self.assertEqual(r['targets'][1]['successful_requests'],2)
        self.assertIsNone(r['comparison'][0]['answer_equal'])

    def test_warmup_failure_keeps_evidence_and_continues(self):
        def jobs(rows,url,*args,**kwargs):
            if url.endswith('8081'):
                return [{'sample_id':r['id'],'outcome':'failed','attempted':True,'elapsed_ms':1,'error_code':'UPSTREAM_TIMEOUT','article':None} for r in rows]
            return self.jobs(rows,url,*args,**kwargs)
        r=self.run_matrix(jobs=jobs)
        self.assertEqual(r['targets'][0]['error_code'],'WARMUP_FAILED')
        self.assertEqual(r['targets'][0]['warmup']['failed_requests'],1)
        self.assertEqual(r['targets'][0]['attempted_requests'],0)
        self.assertEqual(r['targets'][1]['successful_requests'],2)

    def test_existing_output_is_preserved_before_network(self):
        output=self.root/'output';output.mkdir();(output/'keep').write_text('keep')
        ready=Mock()
        with self.assertRaises(BenchmarkError):self.run_matrix(readiness=ready)
        ready.assert_not_called();self.assertEqual((output/'keep').read_text(),'keep')

    def test_startup_failure_is_recorded_and_other_targets_continue(self):
        @contextmanager
        def gateway(target,*args):
            if target['name']=='v2':raise BenchmarkError('GATEWAY_STARTUP_FAILED')
            yield 'http://127.0.0.1:8082'
        r=self.run_matrix(gateway=gateway,warmup=0)
        self.assertEqual(r['targets'][0]['error_code'],'GATEWAY_STARTUP_FAILED')
        self.assertEqual(r['targets'][1]['successful_requests'],2)

    def test_interrupt_preserves_pending_configuration_as_unattempted(self):
        def jobs(*_,**__):raise KeyboardInterrupt()
        r=self.run_matrix(jobs=jobs,warmup=0)
        self.assertEqual(r['status'],'INCOMPLETE')
        self.assertEqual(r['error_code'],'INTERRUPTED')
        self.assertEqual(len(r['targets']),2)
        self.assertTrue(all(x['attempted_requests']==0 for x in r['targets']))

    def test_changed_dataset_does_not_receive_successful_collection_status(self):
        def jobs(*args,**kwargs):
            rows=self.jobs(*args,**kwargs)
            self.data.write_text('[{"id":"changed","question":"Changed"}]',encoding='utf-8')
            return rows
        report=self.run_matrix(jobs=jobs,warmup=0)
        self.assertEqual(report['status'],'INCOMPLETE')
        self.assertEqual(report['error_code'],'DATASET_CHANGED_DURING_RUN')
        self.assertEqual(report['targets'][0]['successful_requests'],2)


class CaptureAndGatewayTests(unittest.TestCase):
    def test_readiness_mode_header_is_checked_without_certifying_model_inference(self):
        from io import BytesIO
        for header,mode,error in (('mock','api','MOCK_RAG_IN_API_MODE'),
                                  ('','mock','RAG_NOT_LABELLED_MOCK'),
                                  ('','api',None)):
            response=Mock();response.__enter__=Mock(return_value=response)
            response.__exit__=Mock(return_value=False)
            response.status=200;response.headers={'X-RAG-Mode':header}
            response.read=BytesIO(b'{"status":"ready"}').read
            with self.subTest(header=header,mode=mode),patch('team3_fullstack.tools.retrieval_api_evaluation.urllib.request.urlopen',return_value=response):
                if error:
                    with self.assertRaises(BenchmarkError) as raised:probe_ready('http://localhost:8001',mode)
                    self.assertEqual(raised.exception.code,error)
                else:
                    self.assertFalse(probe_ready('http://localhost:8001',mode)['model_inference_verified'])

    def test_capture_is_opt_in_and_keeps_validated_complete_and_article(self):
        contract=PublicContract(ROOT)
        default=request_sample(Client(),{'id':'q','question':'Câu hỏi'},contract,.5)
        captured=request_sample(Client(),{'id':'q','question':'Câu hỏi'},contract,.5,capture_response=True)
        self.assertNotIn('complete_response',default)
        self.assertNotIn('article_response',default['article'])
        self.assertEqual(captured['complete_response']['status'],'answered')
        self.assertIsNone(captured['complete_response']['citations'][0]['point'])
        self.assertEqual(captured['article']['article_response']['content'],'Nguyên văn kiểm thử')

    def test_bad_article_does_not_erase_captured_answer(self):
        row=request_sample(Client(bad_article=True),{'id':'q','question':'Câu hỏi'},PublicContract(ROOT),.5,capture_response=True)
        self.assertEqual(row['outcome'],'completed')
        self.assertIn('complete_response',row)
        self.assertEqual(row['article']['outcome'],'failed')
        self.assertNotIn('article_response',row['article'])

    def test_external_gateway_is_never_started_or_stopped(self):
        with tempfile.TemporaryDirectory() as tmp,patch('team3_fullstack.tools.retrieval_api_evaluation.subprocess.Popen') as popen:
            with ManagedGateway({'name':'v2','rag_url':'http://localhost:8001','backend_url':'http://localhost:8080'},tmp) as url:
                self.assertEqual(url,'http://localhost:8080')
            popen.assert_not_called()

    def test_managed_startup_failure_closes_owned_log(self):
        with tempfile.TemporaryDirectory() as tmp:
            jar=Path(tmp)/'backend.jar';jar.write_bytes(b'fixture')
            proc=Mock();proc.poll.return_value=1
            with patch.dict(os.environ,{'SPRING_DATASOURCE_URL':'jdbc:postgresql://127.0.0.1/test','SPRING_DATASOURCE_USERNAME':'test'}),patch('team3_fullstack.tools.retrieval_api_evaluation.subprocess.Popen',return_value=proc) as popen:
                gateway=ManagedGateway({'name':'v2','rag_url':'http://localhost:8001'},tmp,jar,'java')
                with self.assertRaises(BenchmarkError):gateway.__enter__()
                self.assertTrue(gateway.log.closed)
                env=popen.call_args.kwargs['env']
                self.assertEqual(env['SPRING_PROFILES_ACTIVE'],'rag')
                self.assertEqual(env['RAG_BASE_URL'],'http://localhost:8001')

    def test_interrupted_startup_stops_owned_process_and_preserves_interrupt(self):
        for interrupt in (KeyboardInterrupt,SystemExit):
            with self.subTest(interrupt=interrupt.__name__),tempfile.TemporaryDirectory() as tmp:
                jar=Path(tmp)/'backend.jar';jar.write_bytes(b'fixture')
                proc=Mock();proc.pid=12345;proc.poll.return_value=None
                with patch.dict(os.environ,{'SPRING_DATASOURCE_URL':'jdbc:postgresql://127.0.0.1/test','SPRING_DATASOURCE_USERNAME':'test'}), \
                     patch('team3_fullstack.tools.retrieval_api_evaluation.subprocess.Popen',return_value=proc), \
                     patch('team3_fullstack.tools.retrieval_api_evaluation.subprocess.run') as stop_tree, \
                     patch('team3_fullstack.tools.retrieval_api_evaluation.urllib.request.urlopen',side_effect=interrupt):
                    gateway=ManagedGateway({'name':'v2','rag_url':'http://localhost:8001'},tmp,jar,'java')
                    try:
                        with self.assertRaises(interrupt):gateway.__enter__()
                        self.assertTrue(gateway.log.closed)
                        proc.wait.assert_called_once_with(timeout=10)
                        if os.name=='nt':
                            self.assertEqual(stop_tree.call_args.args[0],['taskkill','/PID','12345','/T','/F'])
                        else:
                            proc.terminate.assert_called_once_with()
                    finally:
                        if gateway.log and not gateway.log.closed:gateway.log.close()

    def test_interrupted_startup_falls_back_if_tree_cleanup_cannot_start(self):
        with tempfile.TemporaryDirectory() as tmp:
            jar=Path(tmp)/'backend.jar';jar.write_bytes(b'fixture')
            proc=Mock();proc.pid=12345;proc.poll.return_value=None
            with patch.dict(os.environ,{'SPRING_DATASOURCE_URL':'jdbc:postgresql://127.0.0.1/test','SPRING_DATASOURCE_USERNAME':'test'}), \
                 patch('team3_fullstack.tools.retrieval_api_evaluation.subprocess.Popen',return_value=proc), \
                 patch('team3_fullstack.tools.retrieval_api_evaluation.subprocess.run',side_effect=OSError('cleanup command unavailable')), \
                 patch('team3_fullstack.tools.retrieval_api_evaluation.urllib.request.urlopen',side_effect=KeyboardInterrupt):
                gateway=ManagedGateway({'name':'v2','rag_url':'http://localhost:8001'},tmp,jar,'java')
                try:
                    with self.assertRaises(KeyboardInterrupt):gateway.__enter__()
                    proc.terminate.assert_called_once_with()
                    proc.wait.assert_called_once_with(timeout=10)
                    self.assertTrue(gateway.log.closed)
                finally:
                    if gateway.log and not gateway.log.closed:gateway.log.close()


if __name__=='__main__':unittest.main()
