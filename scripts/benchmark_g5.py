"""Thực nghiệm G5 (VLRA-78): Baseline B0 (BM25, không rerank) so với Target T0 (Hybrid + BGE Rerank).

Hai bước, vì T0 cần Dense + GPU (Colab) còn B0 chạy được trên máy thường:

    # 1. Chạy từng hệ thống; file --out vừa là kết quả vừa là checkpoint (chạy lại thì bỏ qua câu đã xong)
    python scripts/benchmark_g5.py run --system b0 --dataset <test_set.json> --out docs/team2_rag/runs/g5/b0.json
    python scripts/benchmark_g5.py run --system t0 --dataset <test_set.json> --out docs/team2_rag/runs/g5/t0.json

    # 2. Gộp thành báo cáo; Gate 3 của scripts/harness_verify.py tính lại chỉ số từ raw_results
    python scripts/benchmark_g5.py report --b0 docs/team2_rag/runs/g5/b0.json --t0 docs/team2_rag/runs/g5/t0.json

Biến cố định (prompt, model, context, token output) lấy chung từ `.env`; runner ghi cấu hình thực tế
của từng bên và báo cáo liệt kê mọi khác biệt. Dataset không có `split: "test"` phải chạy với
`--exploratory` và kết quả mang nhãn đó.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from team2_rag.llm.service import CLAIMS_MIN_OUTPUT_TOKENS  # noqa: E402
from team2_rag.verification.metrics import summarize_g5_records  # noqa: E402

REPORT_JSON = "g5_b0_vs_t0_report.json"
RETRYABLE = {"LLM_UNAVAILABLE", "LLM_TIMEOUT"}
# Khác biệt hợp lệ giữa hai hệ thống; mọi khóa khác trong config phải giống nhau mới là so sánh công bằng.
SYSTEM_KEYS = {"system", "retriever", "rerank_enabled", "rerank_timeout", "weights"}


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def git_commit() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    except (OSError, subprocess.CalledProcessError):
        return "unknown"


def load_cases(paths: list[Path], exploratory: bool) -> list[dict]:
    cases = [c for p in paths for c in json.loads(p.read_text(encoding="utf-8"))]
    ids = [c["id"] for c in cases]
    if len(ids) != len(set(ids)):
        raise ValueError("Trùng id câu hỏi giữa các file dataset")
    if not exploratory and any(c.get("split") != "test" for c in cases):
        raise ValueError("Dataset có câu không phải split=test; chạy Dev Set thì thêm --exploratory")
    return cases


def system_env(system: str) -> dict:
    env = {"LLM_ALLOW_FALLBACK": "false"}  # không đổi model giữa chừng: đo đúng model đã khai
    if system == "b0":
        return {**env, "RAG_BM25_ONLY": "true", "RAG_RERANK": "false"}
    return {**env, "RAG_BM25_ONLY": "false", "RAG_RERANK": "true"}


def run_config(pipeline, system: str) -> dict:
    s, llm = pipeline.settings, pipeline.llm_service
    return {
        "system": system,
        "retriever": type(pipeline.retriever).__name__,
        "rerank_enabled": pipeline.rerank_enabled,
        "rerank_timeout": pipeline.rerank_timeout,
        "weights": list(getattr(pipeline.retriever, "weights", ()) or ()),
        "top_k": pipeline.top_k,
        "provider": s.provider,
        "model": s.model,
        "temperature": s.temperature,
        # Ghi giá trị thật gửi cho LLM: có claims thì LLMService nâng lên CLAIMS_MIN_OUTPUT_TOKENS.
        "max_output_tokens": max(s.max_output_tokens or 0, CLAIMS_MIN_OUTPUT_TOKENS) if llm.include_claims
        else s.max_output_tokens,
        "max_context_chunks": s.max_context_chunks,
        "max_context_chars": s.max_context_chars,
        "include_claims": llm.include_claims,
        "pipeline_timeout": pipeline.pipeline_timeout,
    }


def ask(pipeline, case: dict) -> dict:
    """Một câu qua Retrieval -> Rerank -> LLM -> Verify. Không gọi pipeline.query vì verify fail ở đó
    thành lỗi 502 và mất câu trả lời; ở đây cần giữ câu trả lời để đếm hallucination."""
    from team2_rag.answer import generate_answer_detailed
    from team2_rag.api.handlers import internal_error_payload
    from team2_rag.errors import classify
    from team2_rag.prompts.context import build_context
    from team2_rag.verification.types import Claim, LLMOutputV2
    from team2_rag.verification.verifier import verify_response

    question = case["question"].strip()
    rec = {"id": case["id"], "question": question, "expected_status": case.get("expected_status"),
           "gold_chunk_ids": list(case.get("gold_chunk_ids") or []), "outcome": "error", "error_code": None,
           "retrieved_chunk_ids": [], "context_chunk_ids": [], "llm_context_chunk_ids": [],
           "rerank_fallback_reason": None, "answer": "", "citations": [], "claims": [], "verification": None}
    t0 = time.monotonic()
    try:
        retrieved = pipeline.retriever.retrieve(question, top_k=pipeline.top_k)
        rec["retrieved_chunk_ids"] = [r.get("chunk_id", "") for r in retrieved.get("results", [])]
        details = pipeline._rerank(retrieved)
        rec["rerank_fallback_reason"] = details.fallback_reason
        candidates = details.output.get("results", [])
        rec["context_chunk_ids"] = [r.get("chunk_id", "") for r in candidates]
        s = pipeline.settings
        rec["llm_context_chunk_ids"] = [c.chunk_id for c in build_context(
            candidates, max_chunks=s.max_context_chunks, max_chars=s.max_context_chars).chunks]
        if not candidates:
            rec["outcome"] = "insufficient_context"
        else:
            gen = generate_answer_detailed(details.output, [], llm_service=pipeline.llm_service,
                                           settings=s, token_budget=pipeline.token_budget)
            resp = gen.response
            rec.update(outcome=resp["status"], answer=resp["answer"], citations=resp["citations"])
            if resp["status"] == "answered":
                claims = [Claim(claim_id=c.claim_id, text=c.text, citation_ids=list(c.citation_ids))
                          for c in gen.claims]
                v = verify_response(LLMOutputV2(status="answered", answer=resp["answer"],
                                                citations=resp["citations"], claims=claims), gen.context)
                rec["claims"] = [c.model_dump(include={"claim_id", "text", "verdict", "supported", "cited_citations"})
                                 for c in v.claim_results]
                sm = v.summary
                rec["verification"] = {"passed": v.passed, **{k: sm.get(k, 0) for k in (
                    "total_claims", "supported_claims", "total_citations", "valid_citations")}}
    except Exception as exc:  # ca lỗi giữ lại trong báo cáo, không bỏ
        rec.update(outcome="error", error_code=internal_error_payload(classify(exc), exc)[1]["error"]["code"],
                   answer=f"{type(exc).__name__}: {exc}"[:300])
    rec["e2e_s"] = round(time.monotonic() - t0, 3)
    return rec


def cmd_run(args) -> None:
    os.chdir(ROOT)
    os.environ.update(system_env(args.system))
    from team2_rag.runtime import build_runtime

    cases = load_cases(args.dataset, args.exploratory)[: args.limit or None]
    out = args.out
    state = json.loads(out.read_text(encoding="utf-8")) if out.exists() else {}
    datasets = [{"path": p.as_posix(), "sha256": sha256_file(p)} for p in args.dataset]
    if state and (state["system"] != args.system or state["datasets"] != datasets):
        raise SystemExit(f"{out} là của lượt khác (system/dataset khác); đổi --out hoặc xoá file")

    rt = build_runtime()
    try:
        pipeline = rt.pipeline
        pipeline.llm_service.include_claims = True  # verify cần claims
        state.update(system=args.system, git_commit=git_commit(), datasets=datasets,
                     label="exploratory" if args.exploratory else "test",
                     config=run_config(pipeline, args.system), records=state.get("records", {}))
        out.parent.mkdir(parents=True, exist_ok=True)
        for i, case in enumerate(cases, 1):
            if case["id"] in state["records"]:
                continue
            # Cùng quy tắc thử lại cho B0 và T0: chỉ lỗi tạm thời của LLM, tối đa --retries lần.
            for attempt in range(1, args.retries + 2):
                rec = ask(pipeline, case)
                if rec["error_code"] not in RETRYABLE or attempt > args.retries:
                    break
                time.sleep(args.throttle * 2)
            rec["attempts"] = attempt
            state["records"][case["id"]] = rec
            out.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
            print(f"[{args.system} {i}/{len(cases)}] {case['id']} {rec['outcome']} {rec['error_code'] or ''}")
            time.sleep(args.throttle)
    finally:
        rt.close()


def build_report(b0: dict, t0: dict) -> dict:
    if b0["datasets"] != t0["datasets"] or set(b0["records"]) != set(t0["records"]):
        raise ValueError("B0 và T0 phải chạy cùng dataset và cùng tập câu hỏi")
    diffs = {k: {"b0": b0["config"].get(k), "t0": t0["config"].get(k)}
             for k in sorted(set(b0["config"]) | set(t0["config"]))
             if k not in SYSTEM_KEYS and b0["config"].get(k) != t0["config"].get(k)}
    systems = {}
    for name, run in (("b0", b0), ("t0", t0)):
        raw = [run["records"][k] for k in sorted(run["records"])]
        systems[name] = {"git_commit": run["git_commit"], "config": run["config"],
                         "metrics": summarize_g5_records(raw), "raw_results": raw}
    return {"label": "test" if b0["label"] == t0["label"] == "test" else "exploratory",
            "datasets": b0["datasets"], "controlled_config_differences": diffs,
            "hallucination_method": "verification/rubric.py: đối chiếu từ vựng, chưa phải kiểm tra ngữ nghĩa sâu",
            "systems": systems}


def fmt(v) -> str:
    return "chưa đo" if v is None else f"{v * 100:.2f}%"


def render_md(rep: dict) -> str:
    m = {k: s["metrics"] for k, s in rep["systems"].items()}
    rows = [("Citation correctness (≥ 90%)", "citation_correctness"), ("Citation coverage", "citation_coverage"),
            ("Hallucination theo câu", "query_hallucination_rate"), ("Hallucination theo claim", "claim_hallucination_rate"),
            ("Từ chối: Precision", "refusal_precision"), ("Từ chối: Recall", "refusal_recall")]
    lines = [f"# G5: B0 (BM25) so với T0 (Hybrid + Rerank), nhãn `{rep['label']}`", "",
             "Dataset: " + ", ".join(f"`{d['path']}` (sha256 `{d['sha256'][:12]}`)" for d in rep["datasets"]), "",
             "| Chỉ số | B0 | T0 |", "| :--- | ---: | ---: |"]
    lines += [f"| {label} | {fmt(m['b0'][k])} | {fmt(m['t0'][k])} |" for label, k in rows]
    for key in ("total", "answered", "insufficient_context", "error"):
        lines.append(f"| Số câu `{key}` | {m['b0']['request_outcomes'][key]} | {m['t0']['request_outcomes'][key]} |")
    lines.append(f"| Lùi về thứ hạng Hybrid do rerank lỗi/quá hạn | {m['b0']['rerank_fallbacks']} | {m['t0']['rerank_fallbacks']} |")
    diffs = rep["controlled_config_differences"]
    lines += ["", "Biến kiểm soát khác nhau giữa B0 và T0: " + json.dumps(diffs, ensure_ascii=False)
              if diffs else "Biến kiểm soát giữa B0 và T0: giống nhau.",
              "", f"Hallucination: {rep['hallucination_method']}.",
              "Câu `error` không vào mẫu số chỉ số chất lượng; số mẫu số từng chỉ số xem `metrics.counts` trong JSON."]
    return "\n".join(lines) + "\n"


def cmd_report(args) -> None:
    rep = build_report(*(json.loads(p.read_text(encoding="utf-8")) for p in (args.b0, args.t0)))
    args.out_dir.mkdir(parents=True, exist_ok=True)
    (args.out_dir / REPORT_JSON).write_text(json.dumps(rep, ensure_ascii=False, indent=2), encoding="utf-8")
    (args.out_dir / REPORT_JSON.replace(".json", ".md")).write_text(render_md(rep), encoding="utf-8")
    print(f"Đã ghi {args.out_dir / REPORT_JSON}")


def main(argv=None) -> None:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = p.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run")
    r.add_argument("--system", choices=("b0", "t0"), required=True)
    r.add_argument("--dataset", type=Path, nargs="+", required=True)
    r.add_argument("--out", type=Path, required=True)
    r.add_argument("--exploratory", action="store_true")
    r.add_argument("--limit", type=int, default=0)
    r.add_argument("--throttle", type=float, default=1.5)
    r.add_argument("--retries", type=int, default=2)
    r.set_defaults(fn=cmd_run)
    g = sub.add_parser("report")
    g.add_argument("--b0", type=Path, required=True)
    g.add_argument("--t0", type=Path, required=True)
    g.add_argument("--out-dir", type=Path, default=ROOT / "docs/team2_rag")
    g.set_defaults(fn=cmd_report)
    args = p.parse_args(argv)
    args.fn(args)


if __name__ == "__main__":
    main()
