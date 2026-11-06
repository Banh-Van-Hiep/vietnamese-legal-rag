import json
from pathlib import Path
import sys
import tempfile
import unittest

TOOLS = Path(__file__).resolve().parents[1] / 'tools'
sys.path.insert(0, str(TOOLS))
from team3_fullstack.tools.latency_report import BenchmarkError
from team3_fullstack.tools.retrieval_api_evaluation import load_matrix, summarize_target, compare_queries, render_markdown


class MatrixContractTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        (self.root/'v2.json').write_text(json.dumps({'version':'v2','method':'hybrid_rrf','top_k':20}), encoding='utf-8')
        self.path = self.root/'matrix.json'
        self.matrix = {'format_version':1, 'selected':'hybrid-v2', 'targets':[
            {'name':'hybrid-v2','rag_url':'http://127.0.0.1:8001','config_path':'v2.json'},
            {'name':'baseline','rag_url':'http://127.0.0.1:8002','backend_url':'http://127.0.0.1:8082'},
        ]}

    def load(self, value=None, **options):
        self.path.write_text(json.dumps(value or self.matrix), encoding='utf-8')
        return load_matrix(self.path, **options)

    def test_selected_config_retains_digest_and_resolves_relative_file(self):
        matrix = self.load(selected_only=True)
        self.assertEqual([x['name'] for x in matrix['targets']], ['hybrid-v2'])
        self.assertEqual(matrix['targets'][0]['configuration']['values']['top_k'], 20)
        self.assertEqual(len(matrix['targets'][0]['configuration']['sha256']), 64)
        self.assertEqual(matrix['provenance'], 'operator-declared; not remote configuration attestation')

    def test_rejects_ambiguous_or_unsafe_target_matrices(self):
        for mutation in ('name','rag_url','backend_url','credential_url','query_url','unknown_selection','sensitive_config'):
            value=json.loads(json.dumps(self.matrix))
            if mutation=='name': value['targets'][1]['name']='hybrid-v2'
            if mutation=='rag_url': value['targets'][1]['rag_url']=value['targets'][0]['rag_url']
            if mutation=='backend_url':
                value['targets'][0]['backend_url']=value['targets'][1]['backend_url']
            if mutation=='credential_url': value['targets'][0]['rag_url']='http://user:private@localhost:8001'
            if mutation=='query_url': value['targets'][0]['rag_url']='http://localhost:8001?key=private'
            if mutation=='unknown_selection': value['selected']='missing'
            if mutation=='sensitive_config':
                (self.root/'v2.json').write_text('{"api_key":"private"}',encoding='utf-8')
            with self.subTest(mutation=mutation), self.assertRaises(BenchmarkError): self.load(value)
            (self.root/'v2.json').write_text('{"version":"v2","top_k":20}',encoding='utf-8')

    def test_unknown_filter_and_duplicate_json_keys_fail(self):
        self.load()
        with self.assertRaises(BenchmarkError): load_matrix(self.path, configuration='absent')
        self.path.write_text('{"format_version":1,"format_version":1}',encoding='utf-8')
        with self.assertRaises(BenchmarkError): load_matrix(self.path)

    def test_invalid_selection_types_and_nested_credentials_are_rejected(self):
        for selected in ([],{},42,True):
            value={**self.matrix,'selected':selected}
            with self.subTest(selected=selected),self.assertRaises(BenchmarkError):
                self.load(value)
        (self.root/'v2.json').write_text('{"dense":{"token":"private"}}',encoding='utf-8')
        with self.assertRaises(BenchmarkError):self.load()


def sample(qid, elapsed, answer='nội dung [C1]', chunk='chunk_v1'):
    return {'sample_id':qid,'warmup':False,'attempted':True,'outcome':'completed','elapsed_ms':elapsed,
        'complete_response':{'status':'answered','answer':answer,'citations':[{'chunkId':chunk,'point':None}]},'article':None}


class ComparisonTests(unittest.TestCase):
    def test_failed_and_warmup_samples_do_not_enter_success_percentiles(self):
        rows=[sample('q1',100),sample('q2',200),{'sample_id':'q3','outcome':'failed','attempted':True,'elapsed_ms':900,'error_code':'UPSTREAM_TIMEOUT','article':None}]
        result=summarize_target({'name':'v2'}, rows, [sample('warm',5000)])
        self.assertEqual(result['successful_requests'],2)
        self.assertEqual(result['failed_requests'],1)
        self.assertEqual(result['latency_seconds']['p95'],.2)
        self.assertEqual(result['warmup']['total_requests'],1)
        self.assertEqual(result['samples'][2]['error_code'],'UPSTREAM_TIMEOUT')

    def test_empty_success_is_null_and_unattempted_is_counted(self):
        row={'sample_id':'q1','outcome':'failed','attempted':False,'elapsed_ms':None,'error_code':'RAG_NOT_READY','article':None}
        result=summarize_target({'name':'v2'},[row],[])
        self.assertIsNone(result['latency_seconds']['p95'])
        self.assertEqual(result['attempted_requests'],0)
        self.assertEqual(result['failed_requests'],1)

    def test_comparison_uses_query_id_and_preserves_metadata_differences(self):
        a=summarize_target({'name':'a'},[sample('q1',10),sample('q2',20)],[])
        b=summarize_target({'name':'b'},[sample('q2',30,chunk='different'),sample('q1',40)],[])
        comparison=compare_queries([{'id':'q1'},{'id':'q2'}],[a,b])
        self.assertTrue(comparison[0]['answer_equal'])
        self.assertTrue(comparison[0]['citation_metadata_equal'])
        self.assertFalse(comparison[1]['citation_metadata_equal'])
        self.assertEqual(comparison[1]['by_configuration']['b']['chunk_ids'],['different'])
        self.assertIn('point',b['samples'][0]['complete_response']['citations'][0])

    def test_comparison_failure_is_not_equal_or_a_quality_score(self):
        a=summarize_target({'name':'a'},[sample('q1',10)],[])
        b=summarize_target({'name':'b'},[{'sample_id':'q1','outcome':'failed','attempted':True,'elapsed_ms':5,'error_code':'SERVICE_UNAVAILABLE','article':None}],[])
        result=compare_queries([{'id':'q1'}],[a,b])[0]
        self.assertFalse(result['all_completed'])
        self.assertIsNone(result['answer_equal'])
        self.assertIsNone(result['citation_metadata_equal'])
        self.assertNotIn('quality_score',result)

    def test_markdown_labels_api_scope_and_empty_latency(self):
        target=summarize_target({'name':'v2'},[{'sample_id':'q1','outcome':'failed','attempted':False,'elapsed_ms':None,'article':None}],[])
        markdown=render_markdown({'mode':'mock','status':'INCOMPLETE','targets':[target],'conditions':{'users':1,'warmup':0,'timeout_seconds':5},'provenance':'operator-declared'})
        self.assertIn('v2',markdown)
        self.assertIn('mock',markdown)
        self.assertIn('—',markdown)
        self.assertNotIn('LIVE_VERIFIED',markdown)


if __name__=='__main__': unittest.main()
