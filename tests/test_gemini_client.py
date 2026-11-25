"""GeminiProvider: ngân sách thời gian theo LLM_TIMEOUT_SECONDS, retry 503, lỗi timeout; transport giả, không gọi mạng."""
import unittest
from unittest.mock import patch

from team2_rag.llm.errors import LLMProviderError, LLMRateLimitError, LLMTimeoutError
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


class CapturingTransport(FakeTransport):
    def __init__(self, *replies):
        super().__init__(*replies)
        self.bodies = []

    def post_json(self, url, headers, body, timeout):
        self.bodies.append(body)
        return super().post_json(url, headers, body, timeout)


REFUSAL = '{"status": "insufficient_context", "answer": "Chưa đủ căn cứ.", "citations": []}'
OK_REFUSAL = HttpResponse(200, {"candidates": [{"content": {"parts": [{"text": REFUSAL}]}, "finishReason": "STOP"}]})


def complete(transport, timeout_seconds=30.0, **kw):
    provider = GeminiProvider("k", "gemini-x", timeout_seconds, transport=transport, **kw)
    return provider.complete(RenderedPrompt("sys", "user"), LLMParams())


class ClaimsOutputCapTests(unittest.TestCase):
    def cap_sent(self, include_claims):
        transport = CapturingTransport(OK_REFUSAL)
        LLMService(GeminiProvider("k", "gemini-x", 30.0, transport=transport), include_claims=include_claims).ask("Câu hỏi?", "context")
        return transport.bodies[0]["generationConfig"]["maxOutputTokens"]

    def test_claims_mode_gets_room_for_the_longer_json(self):
        self.assertEqual(self.cap_sent(True), 4096)  # 1500 làm Gemini cắt cụt JSON (finish=MAX_TOKENS)

    def test_normal_mode_keeps_the_configured_cap(self):
        self.assertEqual(self.cap_sent(False), 1500)


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


class FakeClock:
    def __init__(self):
        self.now, self.sleeps = 100.0, []

    def __call__(self):
        return self.now

    def sleep(self, seconds):
        self.sleeps.append(seconds)
        self.now += seconds  # Đồng hồ phải tiến cùng sleep để không nhầm backoff với pacing.


class GeminiPacingTests(unittest.TestCase):
    def provider(self, *replies, rpm=60):
        transport, clock = FakeTransport(*replies), FakeClock()
        provider = GeminiProvider("k", "gemini-x", transport=transport, rate_limit_rpm=rpm)
        provider._clock, provider._sleep = clock, clock.sleep
        return provider, transport, clock

    def complete(self, provider):
        return provider.complete(RenderedPrompt("sys", "user"), LLMParams())

    def test_consecutive_completions_at_60_rpm_wait_one_second(self):
        provider, transport, clock = self.provider(OK, OK)
        self.complete(provider)
        self.assertEqual(clock.sleeps, [])
        self.complete(provider)
        self.assertEqual(len(transport.calls), 2)
        self.assertEqual(len(clock.sleeps), 1)
        self.assertAlmostEqual(clock.sleeps[0], 1.0)

    def test_503_and_429_retries_wait_for_the_next_slot(self):
        for busy in (BUSY, HttpResponse(429, {"error": {"message": "quota"}})):
            with self.subTest(status=busy.status):
                provider, transport, clock = self.provider(busy, OK, rpm=30)
                self.complete(provider)
                self.assertEqual(len(transport.calls), 2)
                self.assertEqual(transport.calls[0][0], transport.calls[1][0])
                # Interval 2s còn thiếu 0,8s sau backoff retry 1,2s.
                self.assertEqual(len(clock.sleeps), 2)
                self.assertAlmostEqual(clock.sleeps[0], 1.2)
                self.assertAlmostEqual(clock.sleeps[1], 0.8)

    def test_fallback_model_also_waits_for_the_next_slot(self):
        provider, transport, clock = self.provider(BUSY, BUSY, OK, rpm=30)
        self.complete(provider)
        self.assertEqual(len(transport.calls), 3)
        self.assertIn("gemini-flash-lite-latest", transport.calls[-1][0])
        self.assertEqual(len(clock.sleeps), 3)
        self.assertAlmostEqual(clock.sleeps[-1], 2.0)
        self.assertAlmostEqual(clock.now, 104.0)

    def test_close_deadline_rejects_without_another_transport_call(self):
        provider, transport, clock = self.provider(OK, OK, rpm=12)
        self.complete(provider)
        provider.timeout_seconds = 5.5  # Slot kế ở t=105; deadline t=105,5 không đủ thêm 1s.
        with self.assertRaises(LLMRateLimitError):
            self.complete(provider)
        self.assertEqual(len(transport.calls), 1)
        self.assertEqual(clock.sleeps, [])
        self.assertEqual(transport.replies, [OK])

    def test_zero_rpm_does_not_sleep_between_completions(self):
        provider, transport, clock = self.provider(OK, OK, rpm=0)
        self.complete(provider)
        self.complete(provider)
        self.assertEqual(len(transport.calls), 2)
        self.assertEqual(clock.sleeps, [])

    def test_http_status_is_logged_at_warning_for_503_and_info_for_200(self):
        provider, _, _ = self.provider(BUSY, OK)
        with self.assertLogs("team2_rag.llm", "INFO") as logs:
            self.complete(provider)
        messages = [(record.levelname, record.getMessage()) for record in logs.records]
        self.assertTrue(any(level == "WARNING" and "outcome=http status=503" in msg for level, msg in messages))
        self.assertTrue(any(level == "INFO" and "outcome=http status=200" in msg for level, msg in messages))

    def test_transport_error_logs_connection_error_and_reraises(self):
        error = LLMProviderError("kết nối thất bại")
        provider, transport, _ = self.provider(error)
        with self.assertLogs("team2_rag.llm", "WARNING") as logs, self.assertRaises(LLMProviderError) as raised:
            self.complete(provider)
        self.assertIs(raised.exception, error)
        self.assertEqual(len(transport.calls), 1)
        self.assertIn("llm_http", logs.output[0])
        self.assertIn("outcome=connection_error", logs.output[0])
        self.assertNotIn("status=", logs.output[0])

    def test_transport_timeout_logs_timeout_and_reraises(self):
        error = LLMTimeoutError("hết giờ")
        provider, _, _ = self.provider(error)
        with self.assertLogs("team2_rag.llm", "WARNING") as logs, self.assertRaises(LLMTimeoutError) as raised:
            self.complete(provider)
        self.assertIs(raised.exception, error)
        self.assertIn("outcome=timeout", logs.output[0])


if __name__ == "__main__":
    unittest.main()
