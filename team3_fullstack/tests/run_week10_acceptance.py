"""Week10 UI acceptance: isolated PG/Java/browser; labelled mock or separate real RAG."""
from __future__ import annotations

import argparse
from contextlib import ExitStack
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)


def free_port():
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        return listener.getsockname()[1]


def find_pg():
    executable = shutil.which("pg_ctl")
    if executable:
        return Path(executable).parent
    for base in (Path(os.environ.get("ProgramFiles", "C:/Program Files")) / "PostgreSQL",
                 Path("D:/Program Files/PostgreSQL")):
        if base.is_dir():
            for candidate in sorted(base.glob("*/bin"), reverse=True):
                if (candidate / "pg_ctl.exe").is_file():
                    return candidate
    return None


def find_browser():
    for base in (os.environ.get("ProgramFiles(x86)", "C:/Program Files (x86)"),
                 os.environ.get("ProgramFiles", "C:/Program Files")):
        for name in ("Microsoft/Edge/Application/msedge.exe", "Google/Chrome/Application/chrome.exe"):
            if (Path(base) / name).is_file():
                return str(Path(base) / name)
    return None


def stop_owned(process):
    if process.poll() is not None:
        return
    try:
        if os.name == "nt":
            subprocess.run(["taskkill", "/PID", str(process.pid), "/T", "/F"],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                           creationflags=NO_WINDOW, timeout=15)
        else:
            process.terminate()
    except (OSError, subprocess.TimeoutExpired):
        process.terminate()
    try:
        process.wait(timeout=10)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=10)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("mock", "corpus", "live"), default="mock")
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--browser", default=find_browser())
    parser.add_argument("--pg-bin", type=Path, default=find_pg())
    parser.add_argument("--java", default="java")
    parser.add_argument("--node", default="node")
    parser.add_argument("--backend-jar", type=Path)
    parser.add_argument("--skip-build", action="store_true", help="Use an explicitly supplied current-source JAR")
    parser.add_argument("--rag-url", help="Existing real RAG service; never stopped by this runner")
    parser.add_argument("--bm25-only", action="store_true", help="Real-service BM25 smoke; not Hybrid quality acceptance")
    parser.add_argument("--questions", type=Path, help="Live JSON: answered and insufficient_context questions")
    args = parser.parse_args(argv)
    if not args.browser or not args.pg_bin:
        parser.error("Edge/Chrome and PostgreSQL tools required; set --browser and --pg-bin")
    if args.skip_build and not args.backend_jar:
        parser.error("--skip-build requires --backend-jar built against current source")
    if args.backend_jar and not args.skip_build:
        parser.error("Custom JAR requires --skip-build; default build uses its own output")
    if args.mode == "live" and not (args.rag_url or args.bm25_only):
        parser.error("Live mode requires --rag-url or explicit --bm25-only")
    if args.rag_url and args.bm25_only:
        parser.error("--bm25-only configures an owned service; cannot attest the config of --rag-url")
    if args.rag_url and args.mode != "live":
        parser.error("External RAG URL is for live mode; mock/corpus use owned labelled fixtures")
    if args.bm25_only and args.mode != "live":
        parser.error("--bm25-only is a real-service live smoke configuration")
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S-%f")
    out = (args.output_dir or ROOT / "team3_fullstack/backend/target" / ("week10-" + stamp)).resolve()
    out.mkdir(parents=True, exist_ok=False)
    processes, logs = [], []
    pg_started = False
    env = {**os.environ, "PYTHONIOENCODING": "utf-8", "HF_HUB_OFFLINE": "1", "TRANSFORMERS_OFFLINE": "1"}
    summary = {"mode": args.mode, "status": "FAIL", "model_inference_requested": args.mode == "live",
               "model_inference_observed": None if args.mode == "live" else False,
               "retrieval_configuration": "bm25-only smoke" if args.bm25_only else "configured upstream"}
    if args.mode == "mock":
        summary["expected_ids"] = [f"S{i:02}" for i in range(1, 19)]
    pg_data = out / "postgres-data"
    pg_ctl = args.pg_bin / ("pg_ctl.exe" if os.name == "nt" else "pg_ctl")

    def start(command, name, extra=None, cwd=ROOT):
        log = (out / (name + ".log")).open("w", encoding="utf-8")
        logs.append(log)
        process = subprocess.Popen([str(c) for c in command], cwd=cwd, env={**env, **(extra or {})},
                                   stdout=log, stderr=subprocess.STDOUT, creationflags=NO_WINDOW)
        processes.append(process)
        return process

    def run(command, name, cwd=ROOT, timeout=120):
        process = start(command, name, cwd=cwd)
        if process.wait(timeout=timeout):
            raise RuntimeError(name + " failed; see local log")

    def wait(url, process, timeout=90):
        end = time.monotonic() + timeout
        while time.monotonic() < end:
            try:
                with urllib.request.urlopen(url, timeout=2) as reply:
                    return dict(reply.headers)
            except (urllib.error.URLError, OSError):
                if process is not None and process.poll() is not None:
                    raise RuntimeError("Owned service exited before readiness")
                time.sleep(.15)
        raise RuntimeError("Service readiness timeout")

    original_env = {key: os.environ.get(key) for key in
                    ("SPRING_DATASOURCE_URL", "SPRING_DATASOURCE_USERNAME", "SPRING_DATASOURCE_PASSWORD", "CORS_ALLOWED_ORIGINS")}
    try:
        summary["source_commit"] = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT).decode().strip()
        summary["working_diff_files"] = subprocess.check_output(["git", "diff", "--name-only"], cwd=ROOT).decode().splitlines()
        summary["schema_sha256"] = {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                                    for p in (ROOT / "contracts/v0.1").glob("*.schema.json")}
        backend = ROOT / "team3_fullstack/backend"
        if not args.skip_build:
            wrapper = backend / ("mvnw.cmd" if os.name == "nt" else "mvnw")
            run([wrapper, "-q", "package", "-DskipTests"], "backend-build", cwd=backend, timeout=240)
        jar = (args.backend_jar or backend / "target/backend-0.0.1-SNAPSHOT.jar").resolve()
        if not jar.is_file():
            raise RuntimeError("Backend JAR missing")
        source_files = [backend / "pom.xml", *[p for p in (backend / "src/main").rglob("*") if p.is_file()]]
        if args.skip_build and any(p.stat().st_mtime > jar.stat().st_mtime for p in source_files):
            raise RuntimeError("Supplied JAR predates backend source; rebuild without --skip-build")
        summary["backend_source_sha256"] = hashlib.sha256(b"".join(
            p.relative_to(backend).as_posix().encode() + b"\0" + p.read_bytes() for p in sorted(source_files))).hexdigest()
        summary["backend_jar_sha256"] = hashlib.sha256(jar.read_bytes()).hexdigest()
        pg_port, fe_port, cdp_port = free_port(), free_port(), free_port()
        suffix = ".exe" if os.name == "nt" else ""
        run([args.pg_bin / ("initdb" + suffix), "-D", pg_data, "-U", "week10", "--auth=trust", "--encoding=UTF8", "--locale=C"], "pg-init")
        run([pg_ctl, "-D", pg_data, "-l", out / "postgres.log", "-o", f"-h 127.0.0.1 -p {pg_port} -F", "-w", "start"], "pg-start")
        pg_started = True
        run([args.pg_bin / ("createdb" + suffix), "-h", "127.0.0.1", "-p", pg_port, "-U", "week10", "week10"], "pg-database")
        os.environ.update(SPRING_DATASOURCE_URL=f"jdbc:postgresql://127.0.0.1:{pg_port}/week10",
                          SPRING_DATASOURCE_USERNAME="week10", SPRING_DATASOURCE_PASSWORD="")
        fe = f"http://127.0.0.1:{fe_port}"
        os.environ["CORS_ALLOWED_ORIGINS"] = fe
        rag = args.rag_url
        fixture_log = out / "fixture-requests.jsonl"
        if not rag:
            rag_port = free_port()
            rag = f"http://127.0.0.1:{rag_port}"
            factory = "team2_rag.api:create_app" if args.mode == "live" else "team3_fullstack.tests.week10_fixture:create_fixture_app"
            extra = {"EVALUATION_FIXTURE_LOG": str(fixture_log)}
            if args.bm25_only:
                extra.update(RAG_BM25_ONLY="true", RAG_RERANK="false")
            logging_config = out / "python-logging.json"
            logging_config.write_text(json.dumps({"version": 1, "disable_existing_loggers": False,
                "formatters": {"plain": {"format": "%(levelname)s %(name)s %(message)s"}},
                "handlers": {"console": {"class": "logging.StreamHandler", "formatter": "plain", "stream": "ext://sys.stderr"}},
                "root": {"level": "INFO", "handlers": ["console"]}}), encoding="utf-8")
            api = start([sys.executable, "-m", "uvicorn", factory, "--factory", "--host", "127.0.0.1", "--port", rag_port,
                         "--log-config", logging_config], "rag-service", extra)
        else:
            api = None
        headers = wait(rag.rstrip("/") + "/internal/v1/ready", api)
        mock = any(k.lower() == "x-rag-mode" and v.lower() == "mock" for k, v in headers.items())
        if args.mode == "live" and mock:
            raise RuntimeError("Mock upstream rejected in live mode")
        if args.mode == "mock" and not mock:
            raise RuntimeError("Mock upstream must be explicitly labelled")
        summary["upstream_label"] = "mock" if mock else "not-labelled-mock"
        if args.mode == "live":
            from team2_rag.config.settings import load_settings
            settings = load_settings()
            summary["llm_configuration"] = {"provider": settings.provider, "configured_model": settings.model}
        from team2_rag.articles import get_article
        expected = out / "article-expected.json"
        expected.write_text(json.dumps(get_article("luat-59-2020-qh14-v1", "dieu-12"), ensure_ascii=False), encoding="utf-8")
        questions = args.questions
        if args.mode == "live" and questions is None:
            questions = out / "live-questions.json"
            questions.write_text(json.dumps({"answered": "Điều 1 Luật Doanh nghiệp quy định phạm vi điều chỉnh gồm những nội dung nào?",
                                             "insufficient_context": "Cách nấu món bánh pizza ngon tại nhà?"}, ensure_ascii=False), encoding="utf-8")
        from team3_fullstack.tools.retrieval_api_evaluation import ManagedGateway
        with ExitStack() as stack:
            be = stack.enter_context(ManagedGateway({"name": "week10", "rag_url": rag}, out, jar, args.java, startup_timeout=90))
            vite = start([args.node, "node_modules/vite/bin/vite.js", "--host", "127.0.0.1", "--port", fe_port, "--strictPort"], "frontend",
                         {"VITE_API_URL": be, "VITE_MOCK_MODE": "false" if args.mode == "live" else "true", "VITE_DEBUG_LATENCY": "false"}, ROOT / "team3_fullstack/frontend")
            wait(fe, vite)
            browser = start([args.browser, "--headless=new", "--disable-gpu", "--no-first-run", "--disable-background-networking",
                             "--remote-debugging-address=127.0.0.1", f"--remote-debugging-port={cdp_port}",
                             "--user-data-dir=" + str(out / "browser-profile"), "about:blank"], "browser")
            cdp = f"http://127.0.0.1:{cdp_port}"
            wait(cdp + "/json/version", browser)
            extra = {"FE_URL": fe, "BE_URL": be, "RAG_URL": rag, "CDP_URL": cdp, "EVIDENCE_DIR": str(out),
                     "FIXTURE_LOG": str(fixture_log), "ACCEPTANCE_MODE": args.mode, "ARTICLE_EXPECTED": str(expected)}
            if questions:
                extra["LIVE_QUESTIONS"] = str(questions.resolve())
            probe = start([args.node, ROOT / "team3_fullstack/frontend/tests/browser/week10-ui.mjs"], "ui-probe", extra)
            if probe.wait(timeout=480):
                raise RuntimeError("UI cases failed; see ui-results.json")
            report = json.loads((out / "ui-results.json").read_text(encoding="utf-8"))
            rows = report.get("results", [])
            if (not rows or report.get("exceptions") or report.get("status") != "PASS" or
                    any(row.get("status") != "PASS" for row in rows)):
                raise RuntimeError("Incomplete or failed UI acceptance report")
            if args.mode == "mock" and (len(rows) != 18 or
                    sorted(row.get("id", "") for row in rows) != summary["expected_ids"]):
                raise RuntimeError("Mock report must contain exactly S01 through S18")
            summary["passed"] = len(rows)
            summary["total"] = len(rows)
            summary["status"] = "PASS"
    except Exception as error:
        summary["error_type"] = type(error).__name__
        summary["error"] = str(error) if isinstance(error, RuntimeError) else "See local service logs"
    finally:
        cleanup_errors = []
        for process in reversed(processes):
            try:
                stop_owned(process)
            except Exception as error:
                cleanup_errors.append("process:" + type(error).__name__)
        if pg_started or (pg_data / "postmaster.pid").is_file():
            try:
                with (out / "pg-stop.log").open("w", encoding="utf-8") as log:
                    stopped = subprocess.run([str(pg_ctl), "-D", str(pg_data), "-m", "immediate", "-w", "stop"],
                                             stdout=log, stderr=subprocess.STDOUT, creationflags=NO_WINDOW, timeout=30)
                summary["owned_database_stopped"] = stopped.returncode == 0
            except Exception as error:
                summary["owned_database_stopped"] = False
                cleanup_errors.append("database:" + type(error).__name__)
        for log in logs:
            try:
                log.close()
            except Exception as error:
                cleanup_errors.append("log:" + type(error).__name__)
        if args.mode == "live" and (out / "rag-service.log").is_file():
            calls = re.findall(r"llm_call request_id=([a-zA-Z0-9_-]+) provider=([a-zA-Z0-9_-]+) model=([a-zA-Z0-9_./-]+)",
                               (out / "rag-service.log").read_text(encoding="utf-8", errors="replace"))
            summary["observed_llm_calls"] = [{"request_id": trace, "provider": provider, "model": model} for trace, provider, model in calls]
            if calls:
                summary["model_inference_observed"] = True
        for key, value in original_env.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
        summary["owned_processes_stopped"] = all(p.poll() is not None for p in processes)
        summary["cleanup_errors"] = cleanup_errors
        if cleanup_errors or not summary["owned_processes_stopped"] or summary.get("owned_database_stopped") is False:
            summary["status"] = "FAIL"
        if args.mode == "mock" and not (out / "ui-results.json").exists():
            (out / "ui-results.json").write_text(json.dumps({"mode": "mock", "passed": 0, "total": 18,
                "results": [{"id": f"S{i:02}", "status": "NOT_RUN"} for i in range(1, 19)]}, indent=2), encoding="utf-8")
        (out / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"status": summary["status"], "mode": args.mode, "evidence": str(out)}))
    return 0 if summary["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
