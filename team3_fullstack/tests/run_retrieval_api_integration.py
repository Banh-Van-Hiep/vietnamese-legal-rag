"""Integration harness: real Java/PostgreSQL, labelled RAG fixtures, no model inference."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import time
import urllib.request
import urllib.error

ROOT=Path(__file__).resolve().parents[2]


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir',type=Path,required=True)
    parser.add_argument('--runner-python',type=Path,required=True)
    parser.add_argument('--backend-jar',type=Path,required=True)
    parser.add_argument('--java',required=True)
    args=parser.parse_args();out=args.output_dir.resolve();out.mkdir(parents=True,exist_ok=False)
    children=[];handles=[];ports=[]
    base={**os.environ,'PYTHONIOENCODING':'utf-8','HF_HUB_OFFLINE':'1','TRANSFORMERS_OFFLINE':'1'}
    def start_fixture(name,scenario):
        with socket.socket() as listener:listener.bind(('127.0.0.1',0));port=listener.getsockname()[1]
        ports.append(port);url='http://127.0.0.1:'+str(port)
        log=(out/(name+'-server.log')).open('w',encoding='utf-8');handles.append(log)
        env={**base,'EVALUATION_FIXTURE_SCENARIO':scenario,'EVALUATION_FIXTURE_LOG':str(out/(name+'-requests.jsonl'))}
        proc=subprocess.Popen([sys.executable,'-m','uvicorn','team3_fullstack.tests.retrieval_api_fixture:create_fixture_app','--factory','--host','127.0.0.1','--port',str(port)],cwd=ROOT,env=env,stdout=log,stderr=log,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0));children.append(proc)
        deadline=time.monotonic()+30
        while time.monotonic()<deadline:
            try:
                with urllib.request.urlopen(url+'/internal/v1/ready',timeout=2) as response:
                    if response.status==200 and response.headers.get('X-RAG-Mode')=='mock':return {'name':name,'rag_url':url}
            except (urllib.error.URLError,OSError):pass
            if proc.poll() is not None:raise RuntimeError('Fixture process exited')
            time.sleep(.2)
        raise RuntimeError('Fixture readiness timeout')
    def run(name,targets,*,selected_only=False,mode='mock',warmup=1):
        matrix={'format_version':1,'selected':targets[0]['name'],'targets':targets}
        path=out/(name+'-matrix.json');path.write_text(json.dumps(matrix),encoding='utf-8')
        command=[str(args.runner_python.resolve()),'-X','utf8',str(ROOT/'team3_fullstack/tools/evaluate_retrieval_api.py'),
            '--matrix',str(path),'--dataset',str(out/'queries.json'),'--output-dir',str(out/name),'--mode',mode,
            '--warmup',str(warmup),'--timeout-seconds','8','--backend-jar',str(args.backend_jar.resolve()),'--java',args.java]
        if selected_only:command.append('--selected-only')
        with (out/(name+'-runner.log')).open('w',encoding='utf-8') as log:
            process=subprocess.run(command,cwd=ROOT,env=base,stdout=log,stderr=log,timeout=240,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
        return process.returncode,json.loads((out/name/'report.json').read_text(encoding='utf-8')),command
    result={'mode':'MOCK ONLY; real Java/PostgreSQL; no retrieval/reranker/LLM inference','checks':[]}
    try:
        queries=[{'id':'q1','question':'Trụ sở chính của doanh nghiệp đặt ở đâu?'},{'id':'q2','question':'Luật Doanh nghiệp quy định những vấn đề gì?'}]
        (out/'queries.json').write_text(json.dumps(queries,ensure_ascii=False),encoding='utf-8')
        good=start_fixture('hybrid-v2','answered');good['config_path']=str(ROOT/'team1_data/retrieval/retrieval_v2.json')
        empty=start_fixture('baseline','insufficient_context')
        code,report,command=run('matrix',[good,empty])
        assert code==0 and report['status']=='COLLECTED'
        assert all(t['successful_requests']==2 and t['warmup']['total_requests']==1 for t in report['targets'])
        assert report['targets'][0]['article_requests']==2 and report['targets'][1]['article_requests']==0
        assert all(c['all_completed'] and c['answer_equal'] is False for c in report['comparison'])
        samples=[s for t in report['targets'] for s in t['samples']+t['warmup']['samples']]
        assert len({s['client_request_id'] for s in samples})==6
        for target in report['targets']:
            logged=[json.loads(s) for s in (out/(target['name']+'-requests.jsonl')).read_text(encoding='utf-8').splitlines()]
            assert [x['question'] for x in logged]==[queries[0]['question']]+[q['question'] for q in queries]
            assert {x['request_id'] for x in logged}=={s['trace_id'] for s in target['samples']+target['warmup']['samples']}
        result['checks'].append({'case':'two_target_routing_full_capture_same_queries_uuid_trace_warmup','passed':True,'measured_requests':4,'warmup_requests':2})
        before=(out/'baseline-requests.jsonl').read_bytes()
        code,selected,_=run('selected',[good,empty],selected_only=True,warmup=0)
        assert code==0 and len(selected['targets'])==1 and selected['targets'][0]['name']=='hybrid-v2'
        assert (out/'baseline-requests.jsonl').read_bytes()==before
        result['checks'].append({'case':'selected_v2_only_routes_selected_rag_url','passed':True})
        broken=[start_fixture('unavailable','retrieval_unavailable'),start_fixture('bad-citation','invalid_citation'),start_fixture('timeout','timeout')]
        code,errors,_=run('errors',broken,warmup=0)
        assert code==1
        expected={'unavailable':'SERVICE_UNAVAILABLE','bad-citation':'UPSTREAM_INVALID_RESPONSE','timeout':'UPSTREAM_TIMEOUT'}
        for target in errors['targets']:
            assert target['failed_requests']==2
            assert all(s['error_code']==expected[target['name']] for s in target['samples'])
            assert target['latency_seconds']['p95'] is None
        result['checks'].append({'case':'503_502_504_preserved_as_errors_not_insufficient','passed':True,'failed_requests_recorded':6})
        code,blocked,_=run('api-rejects-mock',[good,empty],mode='api',warmup=0)
        assert code==1 and all(t['error_code']=='MOCK_RAG_IN_API_MODE' and t['attempted_requests']==0 for t in blocked['targets'])
        result['checks'].append({'case':'api_mode_rejects_mock_before_queries','passed':True})
        original=(out/'matrix/report.json').read_bytes()
        repeated=subprocess.run(command,cwd=ROOT,env=base,capture_output=True,timeout=30,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
        assert repeated.returncode==2 and (out/'matrix/report.json').read_bytes()==original
        result['checks'].append({'case':'output_collision_preserves_prior_report','passed':True})
        result['dataset_sha256']=hashlib.sha256((out/'queries.json').read_bytes()).hexdigest()
        print(json.dumps(result),flush=True)
    finally:
        for proc in reversed(children):
            if proc.poll() is None:proc.terminate()
            try:proc.wait(timeout=10)
            except subprocess.TimeoutExpired:proc.kill();proc.wait(timeout=5)
        for handle in handles:handle.close()
        result['fixture_processes_stopped']=all(p.poll() is not None for p in children)
        closed={}
        for port in ports:
            with socket.socket() as s:closed[str(port)]=s.connect_ex(('127.0.0.1',port))!=0
        result['fixture_ports_closed']=closed
        (out/'summary.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')


if __name__=='__main__':main()
