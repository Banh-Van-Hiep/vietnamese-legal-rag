"""Owned-process harness for corpus Viewer and G4 runner preparation; PostgreSQL supplied separately."""
import argparse
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[2]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mode', choices=['corpus', 'mock-demo', 'live-demo'], default='corpus')
    parser.add_argument('--output-dir', type=Path, required=True)
    parser.add_argument('--backend-jar', type=Path, required=True)
    parser.add_argument('--java', default='java')
    parser.add_argument('--node', default='node')
    parser.add_argument('--browser', required=True)
    parser.add_argument('--rag-url')
    parser.add_argument('--questions', type=Path)
    parser.add_argument('--ffmpeg', help='Optional ffmpeg binary for G4 video evidence')
    args = parser.parse_args()
    if not os.environ.get('SPRING_DATASOURCE_URL') or not os.environ.get('SPRING_DATASOURCE_USERNAME'):
        parser.error('Set the test database environment first')
    if args.mode == 'live-demo' and (not args.rag_url or not args.questions):
        parser.error('live-demo needs a ready local or remote RAG URL and a questions JSON')
    out = args.output_dir.resolve(); out.mkdir(parents=True, exist_ok=False)
    processes, handles = [], []
    env = {**os.environ, 'PYTHONIOENCODING': 'utf-8', 'HF_HUB_OFFLINE': '1', 'TRANSFORMERS_OFFLINE': '1'}

    def port():
        with socket.socket() as listener:
            listener.bind(('127.0.0.1', 0)); return listener.getsockname()[1]

    def start(command, name, extra=None, cwd=ROOT):
        log = (out / (name + '.log')).open('w', encoding='utf-8'); handles.append(log)
        proc = subprocess.Popen(command, cwd=cwd, env={**env, **(extra or {})}, stdout=log, stderr=log,
                                creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        processes.append(proc); return proc

    def request(url):
        with urllib.request.urlopen(url, timeout=5) as response:
            return json.loads(response.read().decode('utf-8')), response.headers

    def wait(url, proc):
        deadline = time.monotonic() + 90
        while time.monotonic() < deadline:
            try: return request(url)
            except (urllib.error.URLError, ValueError, TimeoutError, OSError):
                if proc.poll() is not None: raise RuntimeError('Owned process exited before readiness')
                time.sleep(.2)
        raise RuntimeError('Owned process readiness deadline')

    summary = {'mode': args.mode, 'live_g4_approved': False}
    try:
        if args.mode == 'live-demo':
            parsed = urlsplit(args.rag_url)
            if (parsed.scheme not in ('http', 'https') or not parsed.hostname or parsed.username or parsed.password
                    or parsed.query or parsed.fragment or parsed.path not in ('', '/')):
                raise ValueError('RAG URL must be an origin without credentials, query or path')
            rag = args.rag_url.rstrip('/')
            readiness, headers = request(rag + '/internal/v1/ready')
            if readiness.get('status') != 'ready' or headers.get('X-RAG-Mode', '').lower() == 'mock':
                raise RuntimeError('live-demo requires a ready service not labelled mock')
        else:
            rag = 'http://127.0.0.1:' + str(port())
            module = 'team2_rag.api:create_app' if args.mode == 'corpus' else 'team3_fullstack.tests.retrieval_api_fixture:create_fixture_app'
            proc = start([sys.executable, '-m', 'uvicorn', module, '--factory', '--host', '127.0.0.1', '--port', rag.rsplit(':', 1)[1]],
                         'article-service', {'RAG_BM25_INDEX': '', 'RAG_DENSE_INDEX': '', 'EVALUATION_FIXTURE_SCENARIO': 'demo'})
            wait(rag + '/internal/v1/health', proc)
        expected, _ = request(rag + '/internal/v1/documents/luat-59-2020-qh14-v1/articles/dieu-1')
        (out / 'article-expected.json').write_text(json.dumps(expected, ensure_ascii=False), encoding='utf-8')
        backend_port, frontend_port, cdp_port = port(), port(), port()
        backend = 'http://127.0.0.1:' + str(backend_port)
        frontend = 'http://127.0.0.1:' + str(frontend_port)
        java = start([args.java, '-Duser.timezone=UTC', '-jar', str(args.backend_jar.resolve())], 'backend',
                     {'SPRING_PROFILES_ACTIVE': 'rag', 'SERVER_PORT': str(backend_port), 'RAG_BASE_URL': rag,
                      'CORS_ALLOWED_ORIGINS': frontend})
        wait(backend + '/api/v1/health', java)
        vite = start([args.node, 'node_modules/vite/bin/vite.js', '--host', '127.0.0.1', '--port', str(frontend_port), '--strictPort'],
                     'frontend', {'VITE_API_URL': backend, 'VITE_MOCK_MODE': 'true' if args.mode == 'mock-demo' else 'false'}, ROOT / 'team3_fullstack/frontend')
        # Vite root is HTML; health-check it without the JSON readiness helper.
        deadline = time.monotonic() + 30
        while True:
            try:
                with urllib.request.urlopen(frontend, timeout=3): break
            except (urllib.error.URLError, OSError):
                if vite.poll() is not None or time.monotonic() > deadline: raise RuntimeError('Frontend unavailable')
                time.sleep(.2)
        cdp = 'http://127.0.0.1:' + str(cdp_port)
        browser = start([args.browser, '--headless=new', '--disable-gpu', '--no-first-run', '--disable-background-networking',
                         '--remote-debugging-address=127.0.0.1', '--remote-debugging-port=' + str(cdp_port),
                         '--user-data-dir=' + str(out / 'browser-profile'), 'about:blank'], 'browser')
        wait(cdp + '/json/version', browser)
        questions = args.questions
        if args.mode == 'mock-demo':
            questions = out / 'fixture-questions.json'
            questions.write_text(json.dumps({'answered': 'fixture-p0', 'insufficient_context': 'fixture-insufficient'}), encoding='utf-8')
        extra = {'FE_URL': frontend, 'BE_URL': backend, 'RAG_URL': rag, 'CDP_URL': cdp, 'EVIDENCE_DIR': str(out),
                 'ACCEPTANCE_MODE': args.mode, 'ARTICLE_EXPECTED': str(out / 'article-expected.json')}
        if questions: extra['QUESTIONS_FILE'] = str(questions.resolve())
        if args.ffmpeg: extra['FFMPEG_PATH'] = str(Path(args.ffmpeg).resolve())
        runner = start([args.node, str(ROOT / 'team3_fullstack/frontend/tests/browser/team3-acceptance.mjs')], 'probe', extra)
        code = runner.wait(timeout=240)
        report = json.loads((out / 'browser-results.json').read_text(encoding='utf-8'))
        summary.update(browser_exit=code, passed=report['passed'], total=report['total'])
        if code: raise RuntimeError('Browser acceptance probe failed; inspect probe.log')
        print(json.dumps(summary))
    finally:
        for proc in reversed(processes):
            if proc.poll() is None:
                if os.name == 'nt':
                    subprocess.run(['taskkill', '/PID', str(proc.pid), '/T', '/F'], stdout=subprocess.DEVNULL,
                                   stderr=subprocess.DEVNULL, creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
                else: proc.terminate()
            try: proc.wait(timeout=10)
            except subprocess.TimeoutExpired: proc.kill(); proc.wait(timeout=5)
        for handle in handles: handle.close()
        summary['owned_processes_stopped'] = all(proc.poll() is not None for proc in processes)
        (out / 'summary.json').write_text(json.dumps(summary, indent=2), encoding='utf-8')


if __name__ == '__main__': main()
