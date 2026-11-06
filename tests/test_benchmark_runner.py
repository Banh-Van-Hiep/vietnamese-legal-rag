"""classify_failure của runner benchmark: timeout/quá tải LLM không được xếp vào lỗi prompt."""
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


if __name__ == "__main__":
    unittest.main()
