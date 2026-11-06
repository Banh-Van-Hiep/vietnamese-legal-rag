"""Live-mode preflight must fail before starting any gateway or browser."""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import unittest

ROOT = Path(__file__).resolve().parents[2]


class AcceptancePreflightTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.out = Path(self.tmp.name) / 'output'
        self.questions = Path(self.tmp.name) / 'questions.json'
        self.questions.write_text('{"answered":"fixture","insufficient_context":"fixture"}')

    def run_cli(self, *extra):
        return subprocess.run([sys.executable, str(ROOT / 'team3_fullstack/tests/run_team3_acceptance.py'),
            '--mode', 'live-demo', '--output-dir', str(self.out), '--browser', 'must-not-start',
            '--backend-jar', 'must-not-start.jar', *extra], cwd=ROOT,
            env={**os.environ, 'SPRING_DATASOURCE_URL': 'jdbc:postgresql://test-only/db',
                 'SPRING_DATASOURCE_USERNAME': 'test-only'}, capture_output=True, text=True, timeout=15)

    def test_missing_handoff_fails_before_output_or_process_creation(self):
        result = self.run_cli()
        self.assertEqual(result.returncode, 2)
        self.assertFalse(self.out.exists())

    def test_mock_or_unready_is_rejected_before_gateway_creation(self):
        for mock, status in ((True, 'ready'), (False, 'initialising')):
            with self.subTest(mock=mock, status=status):
                if self.out.exists():
                    self.out = self.out.parent / 'second-output'
                calls = []
                class ReadyHandler(BaseHTTPRequestHandler):
                    def do_GET(handler):
                        calls.append(handler.path)
                        handler.send_response(200)
                        handler.send_header('Content-Type', 'application/json')
                        if mock: handler.send_header('X-RAG-Mode', 'mock')
                        handler.end_headers(); handler.wfile.write(json.dumps({'status': status}).encode())
                    def log_message(*_): pass
                server = ThreadingHTTPServer(('127.0.0.1', 0), ReadyHandler)
                thread = threading.Thread(target=server.serve_forever, daemon=True); thread.start()
                try:
                    result = self.run_cli('--rag-url', 'http://127.0.0.1:' + str(server.server_port),
                                          '--questions', str(self.questions))
                    self.assertNotEqual(result.returncode, 0)
                    self.assertIn('live-demo requires a ready service not labelled mock', result.stderr)
                    self.assertEqual(calls, ['/internal/v1/ready'])
                    self.assertFalse((self.out / 'backend.log').exists())
                    self.assertTrue(json.loads((self.out / 'summary.json').read_text())['owned_processes_stopped'])
                finally:
                    server.shutdown(); server.server_close(); thread.join(timeout=3)


if __name__ == '__main__': unittest.main()
