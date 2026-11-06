"""Owned-process week8 tests; real UI/Java/PG and labelled HTTP fixture, no models."""
import argparse
from contextlib import ExitStack
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))


def port():
    with socket.socket() as listener:
        listener.bind(('127.0.0.1', 0)); return listener.getsockname()[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mode', choices=['profile', 'ui', 'full'], default='profile')
    parser.add_argument('--output-dir', type=Path, required=True)
    parser.add_argument('--browser', required=True)
    parser.add_argument('--node', default='node')
    parser.add_argument('--java', default='java')
    parser.add_argument('--backend-jar', type=Path)
    parser.add_argument('--runner-python', type=Path)
    args = parser.parse_args()
    if args.mode != 'profile' and (not args.backend_jar or args.mode == 'full' and not args.runner_python
            or not os.environ.get('SPRING_DATASOURCE_URL') or not os.environ.get('SPRING_DATASOURCE_USERNAME')):
        parser.error('UI/full needs backend JAR and test DB; full also needs runner Python')
    out = args.output_dir.resolve(); out.mkdir(parents=True, exist_ok=False)
    env = {**os.environ, 'PYTHONIOENCODING': 'utf-8', 'HF_HUB_OFFLINE': '1', 'TRANSFORMERS_OFFLINE': '1'}
    processes, logs = [], []
    summary = {'mode': args.mode, 'model_inference': False}

    def start(command, name, extra=None, cwd=ROOT):
        log = (out / (name + '.log')).open('w', encoding='utf-8'); logs.append(log)
        process = subprocess.Popen([str(x) for x in command], cwd=cwd, env={**env, **(extra or {})},
            stdout=log, stderr=log, creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        processes.append(process); return process

    def wait(url, process, timeout=60):
        end = time.monotonic() + timeout
        while time.monotonic() < end:
            try:
                with urllib.request.urlopen(url, timeout=2): return
            except (urllib.error.URLError, OSError):
                if process.poll() is not None: raise RuntimeError('Owned process exited before readiness')
                time.sleep(.1)
        raise RuntimeError('Owned process readiness timeout')

    try:
        with ExitStack() as stack:
            fe_port, cdp_port = port(), port()
            frontend, cdp = 'http://127.0.0.1:' + str(fe_port), 'http://127.0.0.1:' + str(cdp_port)
            backend = None
            if args.mode != 'profile':
                from team3_fullstack.tools.retrieval_api_evaluation import ManagedGateway
                if args.mode == 'full':
                    rag_port = port(); rag = 'http://127.0.0.1:' + str(rag_port)
                    fixture = start([sys.executable, '-m', 'uvicorn',
                        'team2_rag.api.mock_app:create_mock_app', '--factory',
                        '--host', '127.0.0.1', '--port', rag_port], 'fixture',
                        {'RAG_MOCK_SCENARIO': 'answered'})
                    wait(rag + '/internal/v1/ready', fixture)
                    # Test-only JMX registration; no new public metrics endpoint.
                    os.environ['SPRING_DATASOURCE_HIKARI_REGISTER_MBEANS'] = 'true'
                    # Isolate Java capacity from the real API factory's single-inference slot.
                    gateway = ManagedGateway({'name': 'week8', 'rag_url': rag}, out, args.backend_jar, args.java)
                    with gateway as capacity_backend:
                        run_load(args, out, capacity_backend, rag, gateway.process.pid, start)
                ui_rag_port = port(); ui_rag = 'http://127.0.0.1:' + str(ui_rag_port)
                fixture = start([sys.executable, '-m', 'uvicorn',
                    'team3_fullstack.tests.retrieval_api_fixture:create_fixture_app', '--factory',
                    '--host', '127.0.0.1', '--port', ui_rag_port], 'ui-fixture',
                    {'EVALUATION_FIXTURE_SCENARIO': 'demo', 'EVALUATION_FIXTURE_LOG': str(out / 'fixture-requests.jsonl')})
                wait(ui_rag + '/internal/v1/ready', fixture)
                os.environ['CORS_ALLOWED_ORIGINS'] = frontend
                backend = stack.enter_context(ManagedGateway({'name': 'week8-ui', 'rag_url': ui_rag}, out, args.backend_jar, args.java))
                summary['backend_url'] = backend
            vite = start([args.node, 'node_modules/vite/bin/vite.js', '--host', '127.0.0.1',
                '--port', fe_port, '--strictPort'], 'frontend', {'VITE_API_URL': backend or 'http://127.0.0.1:1',
                'VITE_MOCK_MODE': 'true', 'VITE_DEBUG_LATENCY': 'true'}, ROOT / 'team3_fullstack/frontend')
            wait(frontend, vite)
            browser = start([args.browser, '--headless=new', '--disable-gpu', '--no-first-run',
                '--disable-background-networking', '--remote-debugging-address=127.0.0.1',
                '--remote-debugging-port=' + str(cdp_port), '--user-data-dir=' + str(out / 'browser-profile'), 'about:blank'], 'browser')
            wait(cdp + '/json/version', browser)
            extra = {'FE_URL': frontend, 'BE_URL': backend or '', 'CDP_URL': cdp, 'EVIDENCE_DIR': str(out)}
            probe = start([args.node, ROOT / 'team3_fullstack/frontend/tests/browser/week8-profile.mjs'], 'render-probe', extra)
            if probe.wait(timeout=120): raise RuntimeError('Render profile failed; inspect render-probe.log')
            if args.mode != 'profile':
                probe = start([args.node, ROOT / 'team3_fullstack/frontend/tests/browser/week8-ui.mjs'], 'ui-probe', extra)
                if probe.wait(timeout=180): raise RuntimeError('Week8 UI checks failed; inspect ui-probe.log')
            summary['status'] = 'PASS'
    except BaseException as error:
        summary.update(status='FAIL', error_type=type(error).__name__)
        raise
    finally:
        for process in reversed(processes):
            if process.poll() is None:
                if os.name == 'nt':
                    subprocess.run(['taskkill', '/PID', str(process.pid), '/T', '/F'], stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL, creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
                else: process.terminate()
            try: process.wait(timeout=10)
            except subprocess.TimeoutExpired: process.kill(); process.wait(timeout=5)
        for log in logs: log.close()
        summary['owned_processes_stopped'] = all(p.poll() is not None for p in processes)
        (out / 'summary.json').write_text(json.dumps(summary, indent=2), encoding='utf-8')
    print(json.dumps(summary))


def run_load(args, out, backend, rag, pid, start):
    monitor = start([args.java, '-Xmx64m', '--add-modules', 'jdk.attach',
        ROOT / 'team3_fullstack/tests/performance/PoolProbe.java', pid, out], 'pool-monitor')
    end = time.monotonic() + 40
    while not (out / 'pool-ready').exists():
        if monitor.poll() is not None or time.monotonic() > end:
            raise RuntimeError('Pool monitor did not become ready')
        time.sleep(.1)
    try:
        time.sleep(1)
        load = start([args.node, ROOT / 'team3_fullstack/frontend/tests/browser/week8-load.mjs'], 'five-session-load',
                     {'BE_URL': backend, 'EVIDENCE_DIR': str(out)})
        if load.wait(timeout=120): raise RuntimeError('Five-session load failed')
        # Separate independent-query workload for the existing Locust phase-timing runner.
        rows = [{'id': f'perf-{i:03}', 'question': f'fixture-latency-{i}'} for i in range(50)]
        (out / 'latency-queries.json').write_text(json.dumps(rows), encoding='utf-8')
        latency = start([args.runner_python.resolve(), '-X', 'utf8', ROOT / 'team3_fullstack/tools/measure_latency.py',
            '--mode', 'mock', '--dataset', out / 'latency-queries.json', '--base-url', backend, '--rag-url', rag,
            '--users', '5', '--warmup', '1', '--timeout-seconds', '10', '--timing-log', out / 'gateway-week8.log',
            '--output', out / 'latency_report_week8.json'], 'latency-runner')
        if latency.wait(timeout=180): raise RuntimeError('Phase-timing load failed')
        report = json.loads((out / 'latency_report_week8.json').read_text(encoding='utf-8'))
        assert report['successful_requests'] == 50 and report['successful_article_requests'] == 50
        assert report['timing_coverage']['matched_successful'] == 50
        assert report['status'] == 'MOCK_ONLY' and not report['latency_api_pass']
        time.sleep(2)
    finally:
        (out / 'pool-stop').write_text('stop')
        monitor.wait(timeout=20)
    rows = [json.loads(s) for s in (out / 'pool-samples.jsonl').read_text().splitlines()]
    assert rows and rows[-1]['active'] == 0 and rows[-1]['awaiting'] == 0
    assert not any(r['awaiting'] for r in rows)
    assert max(r['executor_threads'] for r in rows) <= 10  #8 workers + heartbeat + recovery
    pool = {'samples': len(rows), 'activePeak': max(r['active'] for r in rows),
            'awaitingPeak': max(r['awaiting'] for r in rows), 'totalInitial': rows[0]['total'],
            'totalFinal': rows[-1]['total'], 'activeFinal': rows[-1]['active'],
            'executorThreadsPeak': max(r['executor_threads'] for r in rows),
            'jvmUsedPeakMb': max(r['jvm_used_bytes'] for r in rows) / 1024**2,
            'scope': 'bounded fixture load and idle recovery; not a long-duration leak proof'}
    (out / 'pool-summary.json').write_text(json.dumps(pool, indent=2), encoding='utf-8')


if __name__ == '__main__': main()
