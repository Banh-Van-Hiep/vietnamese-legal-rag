"""VLRA-T3-15 finite Locust benchmark. Patch only the executable process, not imports."""
if __name__ == '__main__':
    import os
    # LocalRunner uses greenlets, not native worker threads. Keep logging's native
    # thread locks on Windows/Python3.12 to avoid greenlet-finalization errors.
    os.environ['LOCUST_SKIP_MONKEY_PATCH'] = '1'
    from gevent import monkey
    monkey.patch_all(thread=False)

import argparse
from collections import Counter
from datetime import datetime, timezone
import importlib.metadata
import json
from pathlib import Path
import subprocess
import sys
import time
from urllib.parse import quote
import uuid

if __package__:
    from .latency_report import (BenchmarkError, PHASES, PublicContract, digest, distribution,
                                 load_dataset, load_timings, origin, read_json, read_sse, strict_json,
                                 validate_dev, write_report)
else:
    from latency_report import (BenchmarkError, PHASES, PublicContract, digest, distribution,
                                load_dataset, load_timings, origin, read_json, read_sse, strict_json,
                                validate_dev, write_report)

ROOT = Path(__file__).resolve().parents[2]


class RequestDeadline(BenchmarkError):
    def __init__(self): super().__init__('REQUEST_DEADLINE')


def error_code(exc):
    return exc.code if isinstance(exc, BenchmarkError) else 'REQUEST_ERROR'


def response_trace(response):
    value = response.headers.get('X-Request-ID')
    try:
        parsed = uuid.UUID(value)
        if parsed.version != 4 or parsed.variant != uuid.RFC_4122 or str(parsed) != value:
            raise ValueError()
        return value
    except (ValueError, TypeError, AttributeError) as exc:
        raise BenchmarkError('INVALID_RESPONSE_TRACE') from exc


def request_sample(client, case, contract, timeout, warmup=False):
    from gevent import Timeout
    rid = str(uuid.uuid4())
    body = {'question':case['question'], 'clientRequestId':rid}
    row = {'sample_id':case['id'], 'client_request_id':rid, 'trace_id':None, 'warmup':warmup,
           'attempted':True, 'outcome':'failed', 'error_code':None, 'elapsed_ms':None, 'article':None}
    response = None; complete = None; start = time.perf_counter()
    try:
        with Timeout(timeout, RequestDeadline()):
            with client.post('/api/v1/chat/stream', data=json.dumps(body, ensure_ascii=False).encode('utf-8'),
                             headers={'Accept':'text/event-stream', 'Content-Type':'application/json; charset=utf-8'},
                             stream=True, catch_response=True, allow_redirects=False, timeout=(min(2,timeout),timeout),
                             name='HTTP headers chat') as response:
                try:
                    if response.status_code != 200: raise BenchmarkError('HTTP_' + str(response.status_code))
                    row['trace_id'] = response_trace(response)
                    complete = read_sse(response.iter_content(chunk_size=None), body, contract)
                    row['elapsed_ms'] = (time.perf_counter()-start)*1000
                    row.update(outcome='completed', answer_status=complete['status'], conversation_id=complete['conversationId'])
                    response.success()
                except Exception as exc:
                    row['outcome'] = 'failed'; row['error_code'] = error_code(exc); response.failure(row['error_code'])
                finally:
                    response.close()
    except Exception as exc:
        row['outcome'] = 'failed'; row['error_code'] = error_code(exc)
    finally:
        if response is not None: response.close()
        if row['elapsed_ms'] is None: row['elapsed_ms'] = (time.perf_counter()-start)*1000
    if row['outcome'] != 'completed' or complete is None: return row
    if not complete['citations']: return row
    citation = complete['citations'][0]
    article = {'trace_id':None, 'document_id':citation['documentId'], 'article_id':citation['articleId'],
               'outcome':'failed', 'error_code':None, 'elapsed_ms':None}
    row['article'] = article
    path = '/api/v1/documents/' + quote(citation['documentId'], safe='') + '?articleId=' + quote(citation['articleId'], safe='')
    response = None; start = time.perf_counter()
    try:
        with Timeout(timeout, RequestDeadline()):
            with client.get(path, headers={'Accept':'application/json'}, stream=True, catch_response=True,
                            allow_redirects=False, timeout=(min(2,timeout),timeout), name='HTTP headers article') as response:
                try:
                    if response.status_code != 200: raise BenchmarkError('HTTP_' + str(response.status_code))
                    article['trace_id'] = response_trace(response)
                    chunks=[]; size=0
                    for chunk in response.iter_content(chunk_size=None):
                        size+=len(chunk)
                        if size>2_000_000: raise BenchmarkError('RESPONSE_TOO_LARGE')
                        chunks.append(chunk)
                    contract.article(strict_json(b''.join(chunks).decode('utf-8')), citation['documentId'], citation['articleId'])
                    article.update(outcome='completed', elapsed_ms=(time.perf_counter()-start)*1000)
                    response.success()
                except Exception as exc:
                    article['outcome']='failed';article['error_code']=error_code(exc);response.failure(article['error_code'])
                finally: response.close()
    except Exception as exc:
        article['outcome']='failed';article['error_code']=error_code(exc)
    finally:
        if response is not None: response.close()
        if article['elapsed_ms'] is None: article['elapsed_ms']=(time.perf_counter()-start)*1000
    return row


def run_jobs(cases, base_url, users, timeout, contract, warmup=False):
    import gevent
    from gevent.event import Event
    from gevent.queue import Queue, Empty
    from locust import HttpUser, task, constant
    from locust.env import Environment
    from locust.event import Events
    from locust.exception import StopUser
    queue = Queue()
    for i, case in enumerate(cases): queue.put((i,case))
    records=[]; done=Event()

    class FiniteUser(HttpUser):
        wait_time=constant(0)
        @task
        def consume(self):
            try: index,case=queue.get_nowait()
            except Empty: raise StopUser()
            row=request_sample(self.client, case, contract, timeout, warmup)
            row['job_index']=index;records.append(row)
            # Native Locust HTTP streaming metrics cover headers; never use their total for the report.
            self.environment.events.request.fire(request_type='SSE', name='terminal chat', response_time=row['elapsed_ms'],
                                                 response_length=0, exception=None if row['outcome']=='completed' else BenchmarkError(row['error_code']),
                                                 context={'trace_id':row['trace_id']})
            if len(records)==len(cases): done.set()

    env=Environment(user_classes=[FiniteUser], events=Events(), host=base_url)
    runner=env.create_local_runner()
    try:
        runner.start(user_count=min(users,len(cases)), spawn_rate=max(1,users))
        # Each job can contain both chat and article. Do not stop when the queue is merely empty.
        done.wait(timeout=max(15, 2*timeout*((len(cases)+users-1)//users)+10))
    finally: runner.quit()
    finished={r['job_index'] for r in records}
    for i,case in enumerate(cases):
        if i not in finished:
            records.append({'job_index':i,'sample_id':case['id'],'warmup':warmup,'attempted':False,
                            'outcome':'failed','error_code':'RUN_DEADLINE','elapsed_ms':None,'article':None})
    return sorted(records,key=lambda r:r['job_index'])


def summarize(samples, timings, mode, rag_origin=None, live_preflight=False):
    measured=[dict(r) for r in samples if not r['warmup']];warm=[dict(r) for r in samples if r['warmup']]
    ok=[r for r in measured if r['outcome']=='completed']
    articles=[r['article'] for r in measured if r.get('article')]
    good_articles=[r for r in articles if r['outcome']=='completed']
    matched=[]
    for row in measured:
        timing=timings.get(row.get('trace_id'),{})
        identity=(bool(timing) and not timing.get('error') and timing.get('client_request_id')==row.get('client_request_id')
                  and timing.get('trace_id')==row.get('trace_id')
                  and (mode!='live' or timing.get('upstream_origin')==rag_origin))
        # The client has already validated complete. Its closing the connection
        # can race the server's final snapshot; connected is diagnostic only.
        valid=(identity and timing.get('outcome')=='completed'
               and all(timing.get('phases_ms',{}).get(p) is not None for p in PHASES)
               )
        if identity:
            row['backend_timing']=timing
        if row['outcome']=='completed' and valid:
            matched.append(timing)
        elif not (identity and row['outcome']=='failed' and timing.get('outcome') in ('failed','discarded')):
            row['timing_error']=timing.get('error','MISSING_OR_INAPPLICABLE_TIMING')
    chat=distribution([r['elapsed_ms'] for r in ok]);article=distribution([r['elapsed_ms'] for r in good_articles])
    verified=(mode=='live' and live_preflight and bool(ok) and len(matched)==len(ok))
    chat_pass=None if chat['p95'] is None else chat['p95']<=45
    article_pass=None if article['p95'] is None else article['p95']<=1
    latency_pass=verified and len(ok)==len(measured) and len(good_articles)==len(articles) and bool(chat_pass and article_pass)
    return {
        'format_version':1,'test_id':'VLRA-T3-15','mode':mode,
        'status':('LIVE_MEASURED' if latency_pass else 'INCOMPLETE_LIVE') if mode=='live' else ('MOCK_ONLY' if mode=='mock' else 'EXPLORATORY'),
        'total_requests':len(measured),'attempted_requests':sum(r.get('attempted',True) for r in measured),
        'successful_requests':len(ok),'failed_requests':len(measured)-len(ok),
        'article_requests':len(articles),'successful_article_requests':len(good_articles),'failed_article_requests':len(articles)-len(good_articles),
        'latency_distribution_seconds':chat,'article_latency_distribution_seconds':article,
        'phases_breakdown_p95_seconds':{p:distribution([t['phases_ms'][p] for t in matched])['p95'] for p in PHASES},
        'backend_total_distribution_seconds':distribution([t['total_ms'] for t in matched]),
        'timing_coverage':{'eligible_successful':len(ok),'matched_successful':len(matched),'missing_or_invalid':len(ok)-len(matched),
                           'matched_failed':sum(r['outcome']=='failed' and r.get('backend_timing',{}).get('outcome') in ('failed','discarded') for r in measured)},
        'thresholds':{'chat_p95_seconds':{'limit':45,'passed':chat_pass},'article_p95_seconds':{'limit':1,'passed':article_pass}},
        'live_target_verified':verified,'latency_api_pass':latency_pass,'viewer_ui_verified':False,
        'answer_status_counts':dict(Counter(r.get('answer_status') for r in ok)),
        'warmup':{'total_requests':len(warm),'failed_requests':sum(r['outcome']!='completed' or bool(r.get('article') and r['article']['outcome']!='completed') for r in warm),'samples':warm},
        'samples':measured,
        'limits':['Client API timing; not browser render time.','AI service phase is HTTP wait plus response validation, not separate retrieval/rerank/LLM timings.',
                  'Native Locust HTTP header statistics are not added to terminal request counts.','Split proof/readiness do not assert legal review or answer quality.',
                  'Pool/recovery/long-duration leak acceptance belongs to T3-16.'],
    }


def preflight_live(args, rows):
    if not args.split_report or not args.timing_log or not args.rag_url:
        raise BenchmarkError('LIVE_INPUTS_REQUIRED')
    validate_dev(args.dataset, rows, read_json(args.split_report))
    from gevent import Timeout
    import requests
    try:
        with Timeout(5, RequestDeadline()):
            with requests.get(args.rag_url+'/internal/v1/ready',timeout=(2,3),allow_redirects=False) as response:
                if (response.status_code!=200 or response.headers.get('X-RAG-MODE','').lower()=='mock'
                        or strict_json(response.content.decode('utf-8')).get('status')!='ready'):
                    raise BenchmarkError('RAG_NOT_READY_OR_MOCK')
    except BenchmarkError: raise
    except Exception as exc: raise BenchmarkError('RAG_NOT_READY_OR_MOCK') from exc
    return True


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mode',required=True,choices=('mock','exploratory','live'))
    parser.add_argument('--dataset',type=Path,required=True)
    parser.add_argument('--base-url',default='http://localhost:8080')
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--users',type=int,default=1)
    parser.add_argument('--warmup',type=int,default=1)
    parser.add_argument('--timeout-seconds',type=float,default=60)
    parser.add_argument('--timing-log',type=Path)
    parser.add_argument('--timing-wait-seconds',type=float,default=5)
    parser.add_argument('--split-report',type=Path)
    parser.add_argument('--rag-url')
    args=parser.parse_args(argv)
    if args.output.exists():
        print('OUTPUT_EXISTS',file=sys.stderr);return 2
    try:
        if (not 1<=args.users<=5 or not 0<=args.warmup<=10
                or not .1<=args.timeout_seconds<=60 or not 0<=args.timing_wait_seconds<=10):
            raise BenchmarkError('INVALID_CONFIGURATION')
        args.base_url=origin(args.base_url)
        if args.rag_url: args.rag_url=origin(args.rag_url)
        if args.output.resolve()==args.dataset.resolve() or args.timing_log and args.output.resolve()==args.timing_log.resolve():
            raise BenchmarkError('OUTPUT_INPUT_COLLISION')
        rows=load_dataset(args.dataset)
        live_ok=preflight_live(args,rows) if args.mode=='live' else False
        contract=PublicContract(ROOT)
        warm=run_jobs([rows[i%len(rows)] for i in range(args.warmup)],args.base_url,1,args.timeout_seconds,contract,True) if args.warmup else []
        warm_failed=any(r['outcome']!='completed' or r.get('article') and r['article']['outcome']!='completed' for r in warm)
        measured=[] if warm_failed else run_jobs(rows,args.base_url,args.users,args.timeout_seconds,contract)
        samples=warm+measured;traces={r['trace_id'] for r in measured if r.get('trace_id')}
        timings={};deadline=time.monotonic()+args.timing_wait_seconds
        while args.timing_log:
            timings=load_timings(args.timing_log,traces)
            if all(r.get('trace_id') in timings for r in measured if r.get('attempted')) or time.monotonic()>=deadline: break
            import gevent
            gevent.sleep(.05)
        report=summarize(samples,timings,args.mode,args.rag_url,live_ok)
        report.update(generated_at=datetime.now(timezone.utc).isoformat().replace('+00:00','Z'),concurrency_level=args.users,
                      planned_requests=len(rows),timeout_seconds=args.timeout_seconds)
        sources=['team3_fullstack/tools/measure_latency.py','team3_fullstack/tools/latency_report.py',
                 'team3_fullstack/backend/src/main/java/com/legalai/backend/chat/stream/TurnTimings.java',
                 'team3_fullstack/backend/src/main/java/com/legalai/backend/chat/stream/StreamService.java',
                 'team3_fullstack/backend/src/main/resources/application-rag.properties']
        report['provenance']={'dataset_sha256':digest(args.dataset),'source_sha256':{p:digest(ROOT/p) for p in sources},
                              'base_origin':args.base_url,'rag_origin':args.rag_url,'dataset_review':'handoff precondition; not asserted by runner',
                              'python':sys.version.split()[0],'locust':importlib.metadata.version('locust')}
        if args.split_report: report['provenance']['split_report_sha256']=digest(args.split_report)
        try:
            report['provenance']['head']=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True,timeout=5).strip()
            report['provenance']['dirty']=bool(subprocess.check_output(['git','status','--porcelain'],cwd=ROOT,timeout=5))
        except (OSError,subprocess.SubprocessError): report['provenance']['head']=None
        fail=(warm_failed or report['failed_requests']>0 or report['failed_article_requests']>0
              or bool(args.timing_log and report['timing_coverage']['missing_or_invalid'])
              or any(t['passed'] is False for t in report['thresholds'].values())
              or args.mode=='live' and not report['latency_api_pass'])
        if fail: report['status']='FAILED' if args.mode!='live' else 'INCOMPLETE_LIVE'
        write_report(args.output,report)
        print(json.dumps({k:report[k] for k in ('status','total_requests','successful_requests','failed_requests','article_requests','timing_coverage')}))
        return 1 if fail else 0
    except BenchmarkError as exc:
        print(exc.code,file=sys.stderr)
        blocked={'format_version':1,'test_id':'VLRA-T3-15','mode':args.mode,'status':'BLOCKED',
                 'error_code':exc.code,'live_target_verified':False,'latency_api_pass':False,'viewer_ui_verified':False}
        try: write_report(args.output,blocked)
        except BenchmarkError: pass
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
