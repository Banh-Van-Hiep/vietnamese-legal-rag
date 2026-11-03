import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from team3_fullstack.tools.latency_report import (
    BenchmarkError, PublicContract, distribution, load_dataset, load_timings,
    read_sse, validate_dev, write_report,
)

ROOT = Path(__file__).resolve().parents[2]
EXAMPLES = json.loads((ROOT / 'contracts/v0.1/public_examples.json').read_text(encoding='utf-8'))


def wire(complete=None, delta=None):
    complete = copy.deepcopy(complete or EXAMPLES['Complete'])
    meta = {k: complete[k] for k in ('conversationId', 'clientRequestId', 'userMessageId', 'assistantMessageId', 'createdAt')}
    frames = [('meta', meta)]
    if complete['status'] == 'answered':
        frames.append(('delta', {'text': complete['answer'] if delta is None else delta}))
    frames.append(('complete', complete))
    return ''.join(': heartbeat\r\n\r\nevent: '+kind+'\r\ndata: '+json.dumps(data, ensure_ascii=False)+'\r\n\r\n' for kind, data in frames).encode('utf-8')


class ReportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.contract = PublicContract(ROOT)

    def test_fragmented_utf8_crlf_comments_and_binding(self):
        raw = wire()
        result = read_sse((raw[i:i+1] for i in range(len(raw))), EXAMPLES['ChatRequest'], self.contract)
        self.assertEqual(result['answer'], EXAMPLES['Complete']['answer'])

    def test_valid_insufficient_has_no_delta_or_lookup(self):
        self.assertEqual(read_sse([wire(EXAMPLES['InsufficientComplete'])], EXAMPLES['ChatRequest'], self.contract)['citations'], [])

    def test_error_truncation_invalid_utf8_and_wrong_delta_fail_safely(self):
        error = b'event: error\ndata: {"error":{"code":"SERVICE_UNAVAILABLE","message":"Private message","retryable":true}}\n\n'
        cases = [(error, 'SERVICE_UNAVAILABLE'), (wire()[:-5], 'TRUNCATED_STREAM'), (b'\xff', 'INVALID_STREAM'), (wire(delta='wrong'), 'INVALID_STREAM')]
        for data, code in cases:
            with self.subTest(code=code), self.assertRaises(BenchmarkError) as ctx:
                read_sse([data], EXAMPLES['ChatRequest'], self.contract)
            self.assertEqual(ctx.exception.code, code)
            self.assertNotIn('Private', str(ctx.exception))
        private_code=error.replace(b'SERVICE_UNAVAILABLE',b'private-code')
        with self.assertRaises(BenchmarkError) as ctx:
            read_sse([private_code], EXAMPLES['ChatRequest'], self.contract)
        self.assertEqual(ctx.exception.code,'UNRECOGNIZED_PUBLIC_ERROR')

    def test_meta_request_mismatch_and_public_semantics_are_rejected(self):
        bad = copy.deepcopy(EXAMPLES['Complete']); bad['clientRequestId'] = '99999999-9999-4999-8999-999999999999'
        with self.assertRaises(BenchmarkError):
            read_sse([wire(bad)], EXAMPLES['ChatRequest'], self.contract)
        bad = copy.deepcopy(EXAMPLES['Complete']); bad['citations'][0]['citationId'] = 'C2'
        with self.assertRaises(BenchmarkError):
            read_sse([wire(bad)], EXAMPLES['ChatRequest'], self.contract)

    def test_nearest_rank_empty_and_no_early_rounding(self):
        result = distribution([i + .001 for i in range(1, 21)])
        self.assertEqual(result['p95'], 19.001 / 1000)
        self.assertEqual(result['p99'], 20.001 / 1000)
        self.assertEqual(distribution([])['p95'], None)
        with self.assertRaises(BenchmarkError):
            distribution([float('nan')])

    def test_dataset_validation_preserves_source_and_rejects_normalized_duplicates(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)/'input.json'; raw = json.dumps([{'id':'a','question':'Câu hỏi'}], ensure_ascii=False).encode()
            path.write_bytes(raw); self.assertEqual(load_dataset(path)[0]['id'], 'a'); self.assertEqual(path.read_bytes(), raw)
            for cases in [[], [{'id':'a','question':'a'}, {'id':' A ','question':'b'}], [{'id':'a','question':'a\u0301'}]]:
                path.write_text(json.dumps(cases), encoding='utf-8')
                with self.assertRaises(BenchmarkError): load_dataset(path)
            path.write_text('[{"id":"a","id":"b","question":"q"}]', encoding='utf-8')
            with self.assertRaises(BenchmarkError): load_dataset(path)

    def test_dev_hash_count_status_and_test_file_are_checked(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)/'dev.json'
            rows = [{'id':str(i),'question':'Câu hỏi '+str(i),'expected_status':'answered','ground_truth':'Đáp án','gold_chunk_ids':['chunk'],'citation':'Điều 1','category':'Fixture','author':'Nhóm kiểm thử'} for i in range(90)]
            path.write_text(json.dumps(rows, ensure_ascii=False), encoding='utf-8')
            proof = {'format_version':1,'status':'split_only','input':{'count':150},'outputs':{'dev':{'count':90,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'status_counts':{'answered':90,'insufficient_context':0}},'test':{'count':60}}}
            validate_dev(path, rows, proof)
            for bad in [{**proof, 'status':'approved'}, {**proof, 'outputs':{**proof['outputs'], 'dev':{**proof['outputs']['dev'], 'sha256':'0'*64}}}]:
                with self.assertRaises(BenchmarkError): validate_dev(path, rows, bad)
            rows[0]['split']='test'
            with self.assertRaises(BenchmarkError): validate_dev(path, rows, proof)

    def test_timing_whitelist_duplicate_and_invalid_phase_are_not_silently_accepted(self):
        row = {'kind':'chat','trace_id':'trace','client_request_id':'req','outcome':'completed','upstream_origin':'http://localhost:8001','phases_ms':{'backend_init':1.,'ai_service':2.,'db_persist':3.,'stream_finish':4.},'total_ms':11.,'transport_connected':True,'secret':'do-not-copy'}
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)/'log.txt'; path.write_text('prefix CHAT_LATENCY '+json.dumps(row)+'\n', encoding='utf-8')
            found = load_timings(path, {'trace'})
            self.assertNotIn('secret', found['trace'])
            path.write_text('CHAT_LATENCY '+json.dumps({**row,'trace_id':['invalid']})+'\n'+'CHAT_LATENCY '+json.dumps(row),encoding='utf-8')
            self.assertNotIn('error',load_timings(path,{'trace'})['trace'])
            path.write_text(('CHAT_LATENCY '+json.dumps(row)+'\n')*2, encoding='utf-8')
            self.assertEqual(load_timings(path, {'trace'})['trace']['error'], 'DUPLICATE_TIMING')
            row['phases_ms']['ai_service']=-1
            path.write_text('CHAT_LATENCY '+json.dumps(row), encoding='utf-8')
            self.assertEqual(load_timings(path, {'trace'})['trace']['error'], 'INVALID_TIMING')

    def test_output_never_overwrites_or_emits_nan(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'report.json'; write_report(path, {'ok':1})
            before=path.read_bytes()
            with self.assertRaises(BenchmarkError): write_report(path, {'ok':2})
            self.assertEqual(path.read_bytes(), before)
            with self.assertRaises(BenchmarkError): write_report(Path(tmp)/'bad.json', {'bad':float('nan')})


if __name__ == '__main__':
    unittest.main()
