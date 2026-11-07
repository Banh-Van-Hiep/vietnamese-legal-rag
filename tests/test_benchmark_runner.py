"""Runner benchmark: classify_failure (hạ tầng LLM không phải lỗi prompt) và diagnose_refusal (tách lỗi retrieval khỏi prompt)."""
import importlib.util
import unittest
from pathlib import Path

from team2_rag.llm.errors import CitationInvalidError, LLMBadOutputError, LLMTimeoutError

SPEC = importlib.util.spec_from_file_location("benchmark_rag_v2", Path(__file__).resolve().parents[1] / "scripts/benchmark_rag_v2.py")
runner = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(runner)


class ClassifyFailureTests(unittest.TestCase):
    def category(self, error):
        return runner.classify_failure({}, None, "error", [], error)

    def test_llm_timeout_is_infrastructure_not_prompt(self):
        self.assertTrue(self.category(LLMTimeoutError("hết giờ")).startswith("hạ tầng LLM"))

    def test_bad_output_is_prompt_and_invalid_citation_is_wrong_source(self):
        self.assertTrue(self.category(LLMBadOutputError("sai form")).startswith("prompt"))
        self.assertTrue(self.category(CitationInvalidError("lệch")).startswith("nguồn sai"))

    def test_non_llm_exception_is_system(self):
        self.assertTrue(self.category(RuntimeError("x")).startswith("hệ thống"))


class DiagnoseRefusalTests(unittest.TestCase):
    def test_run_without_saved_chunks_does_not_guess_a_cause(self):
        self.assertTrue(runner.diagnose_refusal({"status": "insufficient_context"}).startswith("chưa xác định"))

    def test_gold_chunk_missing_from_context_is_retrieval(self):
        record = {"gold_chunk_ids": ["a"], "context_chunk_ids": ["b", "c"]}
        self.assertTrue(runner.diagnose_refusal(record).startswith("retrieval: 0/1"))

    def test_some_gold_chunks_present_is_partial_retrieval(self):
        record = {"gold_chunk_ids": ["a", "b"], "context_chunk_ids": ["a"]}
        self.assertTrue(runner.diagnose_refusal(record).startswith("retrieval một phần: 1/2"))

    def test_all_gold_chunks_present_points_at_prompt_or_llm(self):
        record = {"gold_chunk_ids": ["a"], "context_chunk_ids": ["a", "b"]}
        self.assertTrue(runner.diagnose_refusal(record).startswith("prompt hoặc LLM"))


class CountAbsenceClaimsTests(unittest.TestCase):
    def results(self, *texts):
        return [{"verification_result": {"claim_results": [{"text": t} for t in texts]}}]

    def test_counts_claims_that_say_the_source_has_no_provision(self):
        raw = self.results("LEGAL CONTEXT hiện tại không quy định về biện pháp khắc phục.",
                           "Nghị định 288/2026/NĐ-CP không quy định cụ thể về xử phạt hành vi này.")
        self.assertEqual(runner.count_absence_claims(raw), 2)

    def test_ignores_ordinary_claims_and_conditional_wording(self):
        raw = self.results("Doanh nghiệp phải gửi thông báo chậm nhất 03 ngày.",
                           "Nếu chưa quy định rõ thì mỗi người là đại diện đủ thẩm quyền.")
        self.assertEqual(runner.count_absence_claims(raw), 0)

    def test_record_without_verification_is_skipped(self):
        self.assertEqual(runner.count_absence_claims([{"verification_result": None}, {}]), 0)


if __name__ == "__main__":
    unittest.main()
