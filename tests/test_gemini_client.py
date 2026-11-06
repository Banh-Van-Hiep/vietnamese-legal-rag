"""GeminiProvider: ngân sách thời gian theo LLM_TIMEOUT_SECONDS, retry 503, lỗi timeout; transport giả, không gọi mạng."""
import unittest
from unittest.mock import patch

from team2_rag.llm.errors import LLMTimeoutError
from team2_rag.llm.gemini_client import GeminiProvider
from team2_rag.llm.http import HttpResponse
from team2_rag.llm.service import LLMService
from team2_rag.llm.types import LLMParams
from team2_rag.prompts.render import RenderedPrompt

OK = HttpResponse(200, {"candidates": [{"content": {"parts": [{"text": "{}"}]}, "finishReason": "STOP"}]})
BUSY = HttpResponse(503, {"error": {"message": "high demand"}})


class FakeTransport:
    def __init__(self, *replies):
        self.replies, self.calls = list(replies), []

    def post_json(self, url, headers, body, timeout):
        self.calls.append((url, timeout))
        reply = self.replies.pop(0)
        if isinstance(reply, Exception):
            raise reply
        return reply


REFUSAL = '{"status": "insufficient_context", "answer": "Chưa đủ căn cứ.", "citations": []}'
OK_REFUSAL = HttpResponse(200, {"candidates": [{"content": {"parts": [{"text": REFUSAL}]}, "finishReason": "STOP"}]})


def complete(transport, timeout_seconds=30.0, **kw):
    provider = GeminiProvider("k", "gemini-x", timeout_seconds, transport=transport, **kw)
    return provider.complete(RenderedPrompt("sys", "user"), LLMParams())


class GeminiBudgetTests(unittest.TestCase):
    def test_single_call_may_use_the_whole_configured_budget(self):
        transport = FakeTransport(OK)
        complete(transport, 30.0)
        self.assertGreater(transport.calls[0][1], 29.0)  # trước đây bị cắt ở 12s mỗi lần gọi

    def test_budget_follows_the_setting_instead_of_a_hardcoded_cap(self):
        transport = FakeTransport(OK)
        complete(transport, 20.0)
        self.assertTrue(19.0 < transport.calls[0][1] <= 20.0)

    def test_503_is_retried_once_on_the_same_model_within_the_budget(self):
        transport = FakeTransport(BUSY, OK)
        with patch("time.sleep"):
            complete(transport)
        self.assertEqual([url for url, _ in transport.calls], [transport.calls[0][0]] * 2)
        self.assertIn("gemini-x", transport.calls[0][0])

    def test_persistent_503_falls_back_to_the_backup_model(self):
        transport = FakeTransport(BUSY, BUSY, OK)
        with patch("time.sleep"):
            complete(transport)
        self.assertIn("gemini-flash-lite-latest", transport.calls[-1][0])

    def test_fallback_can_be_disabled_so_benchmark_measures_only_the_configured_model(self):
        transport = FakeTransport(BUSY, BUSY)
        with patch("time.sleep"), self.assertRaises(Exception):
            complete(transport, allow_fallback=False)
        self.assertEqual(len(transport.calls), 2)  # gọi + một lần retry, không có lần gọi model dự phòng
        self.assertTrue(all("gemini-x" in url for url, _ in transport.calls))

    def test_llm_result_reports_the_model_that_actually_answered(self):
        provider = GeminiProvider("k", "gemini-x", 30.0, transport=FakeTransport(BUSY, BUSY, OK_REFUSAL))
        with patch("time.sleep"):
            result = LLMService(provider).ask("Câu hỏi?", "context")
        self.assertEqual(result.model, "gemini-flash-lite-latest")  # không ghi nhầm model đã cấu hình

    def test_transport_timeout_is_reported_as_llm_timeout(self):
        with self.assertRaises(LLMTimeoutError):
            complete(FakeTransport(LLMTimeoutError("hết giờ")))

    def test_budget_below_the_minimum_raises_llm_timeout_instead_of_name_error(self):
        # Ngân sách < 3s: không gọi lần nào, nhánh `resp is None` phải ném LLMTimeoutError (trước đây thiếu import).
        transport = FakeTransport()
        with self.assertRaises(LLMTimeoutError):
            complete(transport, 2.0)
        self.assertEqual(transport.calls, [])


if __name__ == "__main__":
    unittest.main()
