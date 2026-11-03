"""Run comparable queries through Java gateways for preconfigured RAG services."""
if __name__ == '__main__':
    import os
    os.environ['LOCUST_SKIP_MONKEY_PATCH']='1'
    from gevent import monkey
    monkey.patch_all(thread=False)

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import sys

if __package__:
    from .latency_report import BenchmarkError, PublicContract, digest, load_dataset, write_report
    from .measure_latency import run_jobs
    from .retrieval_api_evaluation import ROOT, ManagedGateway, load_matrix, probe_ready, summarize_target, compare_queries, render_markdown
else:
    from latency_report import BenchmarkError, PublicContract, digest, load_dataset, write_report
    from measure_latency import run_jobs
    from retrieval_api_evaluation import ROOT, ManagedGateway, load_matrix, probe_ready, summarize_target, compare_queries, render_markdown


def unattempted(rows,code):
    return [{'sample_id':r['id'],'warmup':False,'attempted':False,'outcome':'failed',
             'error_code':code,'elapsed_ms':None,'article':None} for r in rows]


def evaluate(matrix_path,dataset_path,output_dir,*,mode='api',users=1,warmup=1,timeout=60,
             configuration=None,selected_only=False,backend_jar=None,java=None,
             jobs=run_jobs,readiness=probe_ready,gateway=ManagedGateway):
    if (mode not in ('api','mock') or type(users) is not int or not 1<=users<=5
            or type(warmup) is not int or warmup<0 or not isinstance(timeout,(int,float))
            or isinstance(timeout,bool) or not 0<timeout<=120):
        raise BenchmarkError('INVALID_RUN_SETTINGS')
    matrix=load_matrix(matrix_path,configuration=configuration,selected_only=selected_only)
    rows=load_dataset(dataset_path)
    if warmup>len(rows):raise BenchmarkError('WARMUP_EXCEEDS_DATASET')
    dataset_hash=digest(dataset_path)
    contract=PublicContract(ROOT)
    output=Path(output_dir)
    try:output.mkdir(parents=True,exist_ok=False)
    except FileExistsError as exc:raise BenchmarkError('OUTPUT_EXISTS') from exc
    results=[];fatal_error=None
    try:
        for target in matrix['targets']:
            measured=[];warm=[];observed=None;failure=None;backend=None
            try:
                observed=readiness(target['rag_url'],mode)
                with gateway(target,output,backend_jar,java) as backend:
                    if warmup:
                        warm=jobs(rows[:warmup],backend,users,timeout,contract,warmup=True,capture_response=True)
                    if any(s['outcome']!='completed' or bool(s.get('article') and s['article']['outcome']!='completed') for s in warm):
                        failure='WARMUP_FAILED';measured=unattempted(rows,failure)
                    else:
                        measured=jobs(rows,backend,users,timeout,contract,capture_response=True)
            except BenchmarkError as exc:
                failure=exc.code;measured=unattempted(rows,failure)
            except Exception:
                failure='TARGET_RUN_FAILED';measured=unattempted(rows,failure)
            results.append(summarize_target(target,measured,warm,readiness=observed,error=failure,backend_url=backend))
        if digest(dataset_path)!=dataset_hash:raise BenchmarkError('DATASET_CHANGED_DURING_RUN')
    except BenchmarkError as exc:
        fatal_error=exc.code
    except KeyboardInterrupt:
        fatal_error='INTERRUPTED'
    finally:
        present={r['name'] for r in results}
        for target in matrix['targets']:
            if target['name'] not in present:
                code=fatal_error or 'RUN_FAILED'
                results.append(summarize_target(target,unattempted(rows,code),[],error=code))
        try:source=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True,stderr=subprocess.DEVNULL).strip()
        except (OSError,subprocess.SubprocessError):source=None
        report={'format_version':1,'test_ids':['VLRA-59','VLRA-60','VLRA-61','VLRA-62','VLRA-63'],
            'generated_at':datetime.now(timezone.utc).isoformat(),'source':source,'mode':mode,
            'status':'COLLECTED' if not fatal_error and results and len(results)==len(matrix['targets']) and all(r['status']=='COLLECTED' for r in results) else 'INCOMPLETE',
            'error_code':fatal_error,
            'dataset_sha256':dataset_hash,'matrix_sha256':matrix['sha256'],'selected':matrix['selected'],
            'conditions':{'users':users,'warmup':warmup,'timeout_seconds':timeout,'query_ids':[r['id'] for r in rows],
                'configuration_schedule':'sequential','percentile':'nearest rank; successful measured samples only'},
            'provenance':matrix['provenance'],'model_inference_verified':False,'targets':results,
            'comparison':compare_queries(rows,results),
            'limits':['Declared URL/config hashes do not attest remote runtime/model settings.',
                'API terminal latency includes Java/RAG/DB/transport; not isolated retrieval or UI rendering.',
                'All citations captured; article body verified only for the first citation.',
                'Collection success is not legal correctness, live-model verification or Jira acceptance.']}
        write_report(output/'report.json',report)
        (output/'comparison.md').write_text(render_markdown(report),encoding='utf-8')
    return report


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--matrix',required=True,type=Path)
    parser.add_argument('--dataset',required=True,type=Path)
    parser.add_argument('--output-dir',required=True,type=Path)
    selection=parser.add_mutually_exclusive_group()
    selection.add_argument('--configuration')
    selection.add_argument('--selected-only',action='store_true')
    parser.add_argument('--mode',choices=['api','mock'],default='api')
    parser.add_argument('--users',type=int,default=1)
    parser.add_argument('--warmup',type=int,default=1)
    parser.add_argument('--timeout-seconds',type=float,default=60)
    parser.add_argument('--backend-jar',type=Path)
    parser.add_argument('--java')
    args=parser.parse_args(argv)
    try:
        report=evaluate(args.matrix,args.dataset,args.output_dir,mode=args.mode,users=args.users,warmup=args.warmup,
            timeout=args.timeout_seconds,configuration=args.configuration,selected_only=args.selected_only,
            backend_jar=args.backend_jar,java=args.java)
    except BenchmarkError as exc:
        print(exc.code,file=sys.stderr);return 2
    except (OSError,ValueError):
        print('EVALUATION_INPUT_OR_OUTPUT_ERROR',file=sys.stderr);return 2
    print(render_markdown(report))
    return 0 if report['status']=='COLLECTED' else 1


if __name__=='__main__':sys.exit(main())
