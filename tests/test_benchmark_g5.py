"""VLRA-78 (T2-38..40): runner B0/T0, chỉ số G5 tính từ raw_results và Gate 3 cho báo cáo G5. LLM giả, không gọi mạng."""
import copy
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock

from team2_rag.config.settings import LLMSettings
from team2_rag.llm.errors import LLMTimeoutError
from team2_rag.llm.fake import FakeLLMProvider
from team2_rag.llm.service import LLMService
from team2_rag.pipeline import RAGPipeline
from team2_rag.verification.metrics import summarize_g5_records

ROOT = Path(__file__).resolve().parents[1]
SAMPLE = json.loads((ROOT / "team2_rag/data/samples/reranker_input.json").read_text(encoding="utf-8"))
META = ("chunk_id", "document_id", "article_id", "document_title", "article", "clause", "point", "source_url")


def load_script(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / f"scripts/{name}.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


g5 = load_script("benchmark_g5")
harness = load_script("harness_verify")


def pipeline(reply):
    """Rerank tắt: context giữ thứ tự retrieval, nhãn C2 là dòng 1."""
    payload = copy.deepcopy(SAMPLE)
    retriever = Mock()
    retriever.retrieve.return_value = payload
    return RAGPipeline(retriever, LLMService(FakeLLMProvider([reply]), include_claims=True), rerank_enabled=False,
                       settings=LLMSettings(provider="fake"))


def answered(rows, row=1):
    return {"status": "answered", "answer": "Phản hồi kiểm thử [C2].",
            "citations": [{"citation_id": "C2", **{k: rows[row][k] for k in META}}],
            "claims": [{"claim_id": "K1", "text": rows[row]["content"], "citation_ids": ["C2"]}]}


def rec(i, outcome, expected="answered", v=None, **kw):
    return {"id": f"q{i}", "outcome": outcome, "expected_status": expected, "verification": v,
            "error_code": kw.get("error_code"), "rerank_fallback_reason": kw.get("fallback")}


def verified(passed, claims, supported, cits, valid):
    return {"passed": passed, "total_claims": claims, "supported_claims": supported,
            "total_citations": cits, "valid_citations": valid}


class AskTests(unittest.TestCase):
    CASE = {"id": "q1", "question": SAMPLE["question"], "expected_status": "answered", "gold_chunk_ids": ["x"]}

    def test_answered_keeps_answer_claims_and_verification(self):
        r = g5.ask(pipeline(answered(SAMPLE["results"])), self.CASE)
        self.assertEqual(r["outcome"], "answered")
        self.assertEqual(r["verification"]["total_citations"], 1)
        self.assertEqual(r["claims"][0]["claim_id"], "K1")
        self.assertEqual(r["context_chunk_ids"], [x["chunk_id"] for x in SAMPLE["results"]])
        self.assertEqual(r["rerank_fallback_reason"], "rerank_disabled")

    def test_llm_failure_is_recorded_with_wire_code(self):
        r = g5.ask(pipeline(LLMTimeoutError("quá hạn")), self.CASE)
        self.assertEqual((r["outcome"], r["error_code"]), ("error", "LLM_TIMEOUT"))
        self.assertIn("e2e_s", r)


class SummaryTests(unittest.TestCase):
    def test_metrics_from_raw_records(self):
        rows = [
            rec(1, "answered", v=verified(True, 2, 2, 2, 2)),
            rec(2, "answered", v=verified(False, 2, 1, 2, 1)),
            rec(3, "insufficient_context", "insufficient_context"),  # từ chối đúng
            rec(4, "insufficient_context"),                          # từ chối sai
            rec(5, "answered", "insufficient_context", v=verified(True, 1, 1, 1, 1)),  # đáng lẽ phải từ chối
            rec(6, "error", "insufficient_context", error_code="LLM_UNAVAILABLE"),  # lỗi: ra khỏi mẫu số
        ]
        m = summarize_g5_records(rows)
        self.assertEqual(m["request_outcomes"], {"total": 6, "answered": 3, "insufficient_context": 2, "error": 1})
        self.assertEqual(m["error_breakdown"], {"LLM_UNAVAILABLE": 1})
        self.assertEqual((m["citation_correctness"], m["citation_coverage"]), (0.8, 0.8))
        self.assertEqual((m["query_hallucination_rate"], m["claim_hallucination_rate"]), (0.3333, 0.2))
        self.assertEqual((m["refusal_precision"], m["refusal_recall"]), (0.5, 0.5))

    def test_no_samples_means_not_measured(self):
        m = summarize_g5_records([rec(1, "error", error_code="LLM_TIMEOUT")])
        self.assertIsNone(m["citation_correctness"])
        self.assertIsNone(m["refusal_recall"])

    def test_rerank_fallback_counted_but_disabled_is_not(self):
        rows = [rec(1, "insufficient_context", fallback="RerankTimeout"),
                rec(2, "insufficient_context", fallback="rerank_disabled")]
        self.assertEqual(summarize_g5_records(rows)["rerank_fallbacks"], 1)


class ReportAndGateTests(unittest.TestCase):
    def run_file(self, system, records, **config):
        base = {"top_k": 10, "model": "m", "max_context_chunks": 5}
        return {"system": system, "git_commit": "abc", "label": "test",
                "datasets": [{"path": "team1_data/golden/golden_phase1.json", "sha256": g5.sha256_file(
                    ROOT / "team1_data/golden/golden_phase1.json")}],
                "config": {**base, "system": system, **config}, "records": {r["id"]: r for r in records}}

    def report(self, **t0_config):
        b0 = self.run_file("b0", [rec(1, "answered", v=verified(True, 1, 1, 1, 1)), rec(2, "insufficient_context")])
        t0 = self.run_file("t0", [rec(1, "answered", v=verified(False, 1, 0, 1, 0)), rec(2, "error", error_code="X")],
                           **t0_config)
        return g5.build_report(b0, t0)

    def gate(self, rep):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "g5.json"
            path.write_text(json.dumps(rep, ensure_ascii=False), encoding="utf-8")
            return harness.check_g5_report(path)

    def test_report_passes_gate_and_lists_config_differences(self):
        rep = self.report(model="khác", rerank_enabled=True)
        self.assertEqual(self.gate(rep), [])
        self.assertEqual(rep["controlled_config_differences"], {"model": {"b0": "m", "t0": "khác"}})
        self.assertIn("| Citation correctness", g5.render_md(rep))

    def test_gate_catches_edited_metrics_and_dataset_change(self):
        rep = self.report()
        rep["systems"]["t0"]["metrics"]["citation_correctness"] = 0.95
        rep["datasets"][0]["sha256"] = "0" * 64
        errors = self.gate(rep)
        self.assertTrue(any("t0" in e and "raw_results" in e for e in errors))
        self.assertTrue(any("sha256" in e for e in errors))

    def test_gate_catches_different_question_sets(self):
        rep = self.report()
        rep["systems"]["t0"]["raw_results"] = rep["systems"]["t0"]["raw_results"][:1]
        rep["systems"]["t0"]["metrics"] = summarize_g5_records(rep["systems"]["t0"]["raw_results"])
        self.assertTrue(any("cùng tập câu hỏi" in e for e in self.gate(rep)))

    def test_report_refuses_runs_on_different_questions(self):
        b0 = self.run_file("b0", [rec(1, "insufficient_context")])
        t0 = self.run_file("t0", [rec(2, "insufficient_context")])
        with self.assertRaises(ValueError):
            g5.build_report(b0, t0)

    def test_dataset_path_is_relative_to_repo(self):
        self.assertEqual(g5.repo_path(ROOT / "team1_data/golden/test_set_v1.json"), "team1_data/golden/test_set_v1.json")

    def test_dev_rows_need_exploratory_flag(self):
        path = ROOT / "team1_data/golden/golden_phase1.json"
        with self.assertRaises(ValueError):
            g5.load_cases([path], exploratory=False)
        self.assertEqual(len(g5.load_cases([path], exploratory=True)), 110)


if __name__ == "__main__":
    unittest.main()
