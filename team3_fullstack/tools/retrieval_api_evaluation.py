"""Manifest, process lifecycle and reporting for preconfigured Retrieval API targets."""
from __future__ import annotations

from contextlib import AbstractContextManager
import json
import os
from pathlib import Path
import re
import socket
import subprocess
import time
import urllib.error
import urllib.request

try:
    from .latency_report import BenchmarkError, digest, distribution, origin, read_json
except ImportError:
    from latency_report import BenchmarkError, digest, distribution, origin, read_json

ROOT = Path(__file__).resolve().parents[2]
PROVENANCE = 'operator-declared; not remote configuration attestation'
SENSITIVE = {'api_key','apikey','password','secret','credentials','authorization',
             'token','access_token','refresh_token','private_key','client_secret'}
CONFIG_FIELDS = {'name','version','status','method','top_k','bm25','dense','hybrid','chunking',
                 'legal_status','rrf_k','weights','embedder','reranker'}


def load_configuration(path):
    value = read_json(path)
    if not isinstance(value,dict): raise BenchmarkError('INVALID_CONFIGURATION_FILE')
    def inspect(item):
        if isinstance(item,dict):
            if any(k.lower() in SENSITIVE or k.lower().endswith('_api_key') for k in item):
                raise BenchmarkError('SENSITIVE_CONFIGURATION')
            for v in item.values(): inspect(v)
        elif isinstance(item,list):
            for v in item: inspect(v)
    inspect(value)
    return {'source_name':Path(path).name,'sha256':digest(path),
            'values':{k:v for k,v in value.items() if k in CONFIG_FIELDS}}


def load_matrix(path, *, configuration=None, selected_only=False):
    path=Path(path);value=read_json(path)
    if (not isinstance(value,dict) or type(value.get('format_version')) is not int
            or value['format_version']!=1 or not isinstance(value.get('targets'),list) or not value['targets']):
        raise BenchmarkError('INVALID_MATRIX')
    names=set();rags=set();backends=set();targets=[]
    for row in value['targets']:
        if not isinstance(row,dict) or not isinstance(row.get('name'),str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]{0,63}',row['name']):
            raise BenchmarkError('INVALID_TARGET_NAME')
        name=row['name'];rag=origin(row.get('rag_url'))
        backend=origin(row['backend_url']) if row.get('backend_url') else None
        if name.casefold() in names or rag in rags or (backend and backend in backends):
            raise BenchmarkError('DUPLICATE_TARGET')
        names.add(name.casefold());rags.add(rag)
        if backend: backends.add(backend)
        source=None
        if row.get('config_path'):
            if not isinstance(row['config_path'],str): raise BenchmarkError('INVALID_CONFIGURATION_FILE')
            source=load_configuration((path.parent/row['config_path']).resolve())
        targets.append({'name':name,'rag_url':rag,'backend_url':backend,'configuration':source})
    selected=value.get('selected')
    target_names={t['name'] for t in targets}
    if selected is not None and (not isinstance(selected,str) or selected not in target_names):
        raise BenchmarkError('UNKNOWN_CONFIGURATION')
    requested=selected if selected_only else configuration
    if selected_only and selected is None: raise BenchmarkError('MISSING_SELECTED_CONFIGURATION')
    if requested is not None:
        if requested not in target_names: raise BenchmarkError('UNKNOWN_CONFIGURATION')
        targets=[t for t in targets if t['name']==requested]
    return {'format_version':1,'sha256':digest(path),'selected':selected,'targets':targets,'provenance':PROVENANCE}


def probe_ready(base_url, mode):
    try:
        with urllib.request.urlopen(base_url+'/internal/v1/ready',timeout=5) as response:
            body=json.loads(response.read(16384).decode('utf-8'))
            mock=response.headers.get('X-RAG-Mode','').lower()=='mock'
            if response.status!=200 or not isinstance(body,dict) or body.get('status')!='ready':
                raise BenchmarkError('RAG_NOT_READY')
            if mock and mode!='mock': raise BenchmarkError('MOCK_RAG_IN_API_MODE')
            if mode=='mock' and not mock: raise BenchmarkError('RAG_NOT_LABELLED_MOCK')
            return {'http_status':200,'observed_mock_header':mock,'model_inference_verified':False}
    except BenchmarkError: raise
    except (urllib.error.URLError,ValueError,UnicodeError,TimeoutError,OSError) as exc:
        raise BenchmarkError('RAG_NOT_READY') from exc


class ManagedGateway(AbstractContextManager):
    """One owned Java gateway. Never starts/stops the supplied RAG service."""
    def __init__(self,target,output,backend_jar=None,java=None,startup_timeout=60):
        self.target,self.output=target,Path(output)
        self.jar=Path(backend_jar).resolve() if backend_jar else None
        suffix='java.exe' if os.name=='nt' else 'java'
        self.java=java or (str(Path(os.environ['JAVA_HOME'])/'bin'/suffix) if os.environ.get('JAVA_HOME') else 'java')
        self.startup_timeout=startup_timeout;self.process=None;self.log=None

    def __enter__(self):
        if self.target.get('backend_url'): return self.target['backend_url']
        if not self.jar or not self.jar.is_file(): raise BenchmarkError('BACKEND_JAR_REQUIRED')
        if not os.environ.get('SPRING_DATASOURCE_URL') or not os.environ.get('SPRING_DATASOURCE_USERNAME'):
            raise BenchmarkError('DATABASE_CONFIGURATION_REQUIRED')
        with socket.socket() as listener:
            listener.bind(('127.0.0.1',0));port=listener.getsockname()[1]
        base='http://127.0.0.1:'+str(port)
        env={**os.environ,'SPRING_PROFILES_ACTIVE':'rag','SERVER_PORT':str(port),
             'RAG_BASE_URL':self.target['rag_url'],'CHAT_LATENCY_ENABLED':'true'}
        self.log=(self.output/('gateway-'+self.target['name']+'.log')).open('w',encoding='utf-8')
        try:
            self.process=subprocess.Popen([str(self.java),'-jar',str(self.jar)],cwd=ROOT,env=env,
                stdout=self.log,stderr=self.log,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
            end=time.monotonic()+self.startup_timeout
            while time.monotonic()<end:
                if self.process.poll() is not None: raise BenchmarkError('GATEWAY_STARTUP_FAILED')
                try:
                    with urllib.request.urlopen(base+'/api/v1/health',timeout=2) as response:
                        if response.status==200:return base
                except (urllib.error.URLError,TimeoutError,OSError): pass
                time.sleep(.2)
            raise BenchmarkError('GATEWAY_STARTUP_TIMEOUT')
        except OSError as exc:
            self.__exit__(None,None,None);raise BenchmarkError('GATEWAY_STARTUP_FAILED') from exc
        except BaseException:
            # __exit__ is not called automatically when __enter__ is interrupted.
            self.__exit__(None,None,None)
            raise

    def __exit__(self,*_):
        try:
            if self.process is not None and self.process.poll() is None:
                if os.name=='nt':
                    try:
                        subprocess.run(['taskkill','/PID',str(self.process.pid),'/T','/F'],
                            stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
                    except OSError:
                        self.process.terminate()
                else: self.process.terminate()
                try:self.process.wait(timeout=10)
                except subprocess.TimeoutExpired:self.process.kill();self.process.wait(timeout=5)
        finally:
            if self.log:self.log.close()
        return False


def summarize_target(target,samples,warmup,*,readiness=None,error=None,backend_url=None):
    good=[r for r in samples if r['outcome']=='completed']
    articles=[r['article'] for r in samples if r.get('article')]
    good_articles=[a for a in articles if a['outcome']=='completed']
    warm_failed=sum(r['outcome']!='completed' or bool(r.get('article') and r['article']['outcome']!='completed') for r in warmup)
    complete=(len(good)==len(samples) and bool(samples) and not warm_failed and len(articles)==len(good_articles) and not error)
    return {**target,'backend_url':backend_url or target.get('backend_url'),'status':'COLLECTED' if complete else 'INCOMPLETE',
        'readiness':readiness,'error_code':error,'provenance':PROVENANCE,
        'total_requests':len(samples),'attempted_requests':sum(r.get('attempted',True) for r in samples),
        'successful_requests':len(good),'failed_requests':len(samples)-len(good),
        'article_requests':len(articles),'failed_article_requests':len(articles)-len(good_articles),
        'latency_seconds':distribution([r['elapsed_ms'] for r in good]),
        'article_latency_seconds':distribution([r['elapsed_ms'] for r in good_articles]),
        'warmup':{'total_requests':len(warmup),'failed_requests':warm_failed,'samples':warmup},'samples':samples}


def compare_queries(queries,results):
    maps={r['name']:{s['sample_id']:s for s in r['samples']} for r in results}
    comparisons=[]
    for q in queries:
        values={};answers=[];citations=[]
        for name,rows in maps.items():
            row=rows.get(q['id'],{});complete=row.get('complete_response') or {}
            c=complete.get('citations',[])
            values[name]={'outcome':row.get('outcome','not_attempted'),'error_code':row.get('error_code'),
                'answer_status':complete.get('status'),'chunk_ids':[x['chunkId'] for x in c]}
            if row.get('outcome')=='completed' and complete:
                answers.append(complete['answer']);citations.append(json.dumps(c,ensure_ascii=False,sort_keys=True))
        all_completed=len(answers)==len(results) and bool(results)
        comparisons.append({'sample_id':q['id'],'all_completed':all_completed,
            'answer_equal':len(set(answers))==1 if all_completed else None,
            'citation_metadata_equal':len(set(citations))==1 if all_completed else None,'by_configuration':values})
    return comparisons


def render_markdown(report):
    conditions=report['conditions']
    lines=['# Retrieval API comparison','',f"Mode: {report['mode']}. Collection: {report['status']}.",
        f"Users: {conditions['users']}; warm-up per target: {conditions['warmup']}; deadline: {conditions['timeout_seconds']}s.",
        'Scope: public API request to validated terminal SSE; first-citation article checked separately.',
        'Percentiles: nearest rank, successful measured requests only; warm-up/errors kept separately.',
        'Configuration provenance is operator-declared; this report does not certify remote models or legal correctness.','',
        '| Configuration | Success/total | Errors | p50 ms | p95 ms | Warm-up errors |',
        '| --- | --- | --- | --- | --- | --- |']
    def ms(v):return '—' if v is None else f'{v*1000:.2f}'
    for r in report['targets']:
        lines.append(f"| {r['name']} | {r['successful_requests']}/{r['total_requests']} | {r['failed_requests']} | {ms(r['latency_seconds']['p50'])} | {ms(r['latency_seconds']['p95'])} | {r['warmup']['failed_requests']} |")
    lines+=['','Raw responses, citation metadata, trace IDs, failures and per-query comparisons: report.json.']
    return '\n'.join(lines)+'\n'
