"""Unit tests for NFR-08 timeout chain (45s AI / 50s Java / 60s FE) and concurrency slot lock (VLRA-T2-33)."""
from __future__ import annotations

import threading
import time
import pytest

pytest.importorskip("httpx")
from fastapi.testclient import TestClient

from team2_rag.api.app import create_app
from team2_rag.llm.errors import LLMTimeoutError
from team2_rag.llm.fake import FakeLLMProvider
from team2_rag.llm.service import LLMService
from team2_rag.pipeline import RAGPipeline
from team2_rag.tests.test_rerank_to_answer import reply_for, retrieval_output


class SlowRetriever:
    def __init__(self, delay_s: float):
        self.delay_s = delay_s

    def retrieve(self, question: str, top_k: int = 10) -> dict:
        time.sleep(self.delay_s)
        return {**retrieval_output(2), "question": question}


class RecordingTimeoutProvider(FakeLLMProvider):
    def __init__(self, responses, timeout_seconds: float = 30.0):
        super().__init__(responses)
        self.timeout_seconds = timeout_seconds
        self.recorded_timeouts: list[float] = []

    def complete(self, prompt, params):
        self.recorded_timeouts.append(self.timeout_seconds)
        return super().complete(prompt, params)


def test_pipeline_passes_remaining_deadline_to_llm():
    """VLRA-T2-33: RAGPipeline.query must shrink LLM timeout to remaining - 0.5s when retrieval takes time."""
    rows = retrieval_output(2)["results"]
    provider = RecordingTimeoutProvider([reply_for(rows, 0)], timeout_seconds=30.0)
    llm = LLMService(provider)
    pipe = RAGPipeline(
        SlowRetriever(delay_s=0.2),
        llm,
        rerank_enabled=False,
        strict_rerank=False,
        pipeline_timeout=10.0,
    )
    out = pipe.query("Luật Doanh nghiệp quy định gì?", [])
    assert out["status"] == "answered"
    assert len(provider.recorded_timeouts) == 1
    assert 8.5 <= provider.recorded_timeouts[0] <= 9.5
    assert provider.timeout_seconds == 30.0


def test_pipeline_aborts_before_llm_when_remaining_under_1s():
    """VLRA-T2-33: If < 1.0s remains before LLM call, pipeline raises LLMTimeoutError without calling LLM."""
    rows = retrieval_output(2)["results"]
    provider = RecordingTimeoutProvider([reply_for(rows, 0)], timeout_seconds=30.0)
    pipe = RAGPipeline(
        SlowRetriever(delay_s=0.25),
        LLMService(provider),
        rerank_enabled=False,
        strict_rerank=False,
        pipeline_timeout=1.1,
    )
    with pytest.raises(LLMTimeoutError):
        pipe.query("Luật Doanh nghiệp quy định gì?", [])
    assert provider.recorded_timeouts == []


def test_nfr08_api_shield_timeout_and_slot_concurrency_lock():
    """VLRA-T2-33: API enforces 45s ceiling (504 LLM_TIMEOUT) and rejects concurrent request with 503 LLM_UNAVAILABLE."""
    started, release = threading.Event(), threading.Event()

    class BlockingPipe:
        def query(self, q, h, request_id=None, deadline=None):
            started.set()
            release.wait(5.0)
            return {"status": "insufficient_context", "answer": "Chưa đủ căn cứ.", "citations": []}

    app = create_app(BlockingPipe(), timeout_seconds=0.1, max_waiting=0)
    with TestClient(app, raise_server_exceptions=False) as c:
        r_timeout = c.post("/internal/v1/query", json={"question": "Câu hỏi 1?", "history": []})
        assert r_timeout.status_code == 504
        assert r_timeout.json()["error"]["code"] == "LLM_TIMEOUT"
        assert r_timeout.json()["error"]["retryable"] is True

        assert started.wait(1.0)
        r_busy = c.post("/internal/v1/query", json={"question": "Câu hỏi 2?", "history": []})
        assert r_busy.status_code == 503
        assert r_busy.json()["error"]["code"] == "LLM_UNAVAILABLE"
        assert r_busy.json()["error"]["retryable"] is True
        release.set()


# ---------------------------------------------------------------- hàng đợi có giới hạn (ADR 0004, VLRA-80)
ANSWER = {"status": "insufficient_context", "answer": "Chưa đủ căn cứ.", "citations": []}
BODY = {"question": "Câu hỏi?", "history": []}


class GatePipe:
    """Ghi số lượt chạy cùng lúc; `release` giữ lượt đầu để các lượt sau phải xếp hàng."""
    def __init__(self, release=None, hold_s=0.0):
        self.release, self.hold_s = release, hold_s
        self.running = self.peak = self.calls = 0
        self.deadlines, self.started, self.lock = [], threading.Event(), threading.Lock()

    def query(self, q, h, request_id=None, deadline=None):
        with self.lock:
            self.running += 1
            self.calls += 1
            self.peak = max(self.peak, self.running)
            self.deadlines.append(deadline)
        self.started.set()
        try:
            if self.release:
                self.release.wait(5.0)
            time.sleep(self.hold_s)
            return ANSWER
        finally:
            with self.lock:
                self.running -= 1


def post_all(client, n):
    out = [None] * n
    threads = [threading.Thread(target=lambda i=i: out.__setitem__(i, client.post("/internal/v1/query", json=BODY)))
               for i in range(n)]
    for t in threads:
        t.start()
    return threads, out


def test_five_concurrent_queries_wait_in_line_and_all_succeed():
    pipe = GatePipe(hold_s=0.05)
    with TestClient(create_app(pipe, timeout_seconds=5)) as c:
        threads, out = post_all(c, 5)
        for t in threads:
            t.join(10)
    assert [r.status_code for r in out] == [200] * 5
    assert (pipe.calls, pipe.peak) == (5, 1)  # vẫn chỉ một lượt chạy tại một thời điểm


def test_full_queue_rejects_with_503_then_recovers():
    release = threading.Event()
    pipe = GatePipe(release=release)
    with TestClient(create_app(pipe, timeout_seconds=5, max_waiting=1)) as c:
        threads, out = post_all(c, 1)
        assert pipe.started.wait(2)
        waiting, waiting_out = post_all(c, 1)
        time.sleep(0.2)  # lượt thứ hai đã vào hàng đợi
        busy = c.post("/internal/v1/query", json=BODY)
        assert busy.status_code == 503
        assert (busy.json()["error"]["code"], busy.json()["error"]["retryable"]) == ("LLM_UNAVAILABLE", True)
        release.set()
        for t in threads + waiting:
            t.join(10)
        assert out[0].status_code == waiting_out[0].status_code == 200
        assert c.post("/internal/v1/query", json=BODY).status_code == 200


def test_waiting_past_deadline_is_504_and_never_starts():
    release = threading.Event()
    pipe = GatePipe(release=release)
    with TestClient(create_app(pipe, timeout_seconds=0.3)) as c:
        threads, out = post_all(c, 1)
        assert pipe.started.wait(2)
        late = c.post("/internal/v1/query", json=BODY)  # chờ quá 0.3 s trong hàng
        assert late.status_code == 504 and late.json()["error"]["code"] == "LLM_TIMEOUT"
        release.set()
        threads[0].join(10)
    assert pipe.calls == 1  # lượt quá hạn không chạy pipeline


def test_api_passes_one_deadline_counted_from_arrival():
    pipe = GatePipe()
    with TestClient(create_app(pipe, timeout_seconds=5)) as c:
        before = time.monotonic()
        assert c.post("/internal/v1/query", json=BODY).status_code == 200
    assert before < pipe.deadlines[0] <= before + 5.1


def test_pipeline_uses_earlier_deadline_from_queue():
    """Đã chờ trong hàng thì LLM chỉ còn phần thời gian còn lại, không được cấp lại `pipeline_timeout`."""
    rows = retrieval_output(2)["results"]
    provider = RecordingTimeoutProvider([reply_for(rows, 0)], timeout_seconds=30.0)
    pipe = RAGPipeline(SlowRetriever(delay_s=0.0), LLMService(provider), rerank_enabled=False,
                       strict_rerank=False, pipeline_timeout=45.0)
    assert pipe.query("Luật Doanh nghiệp quy định gì?", [], deadline=time.monotonic() + 5.0)["status"] == "answered"
    assert 4.0 <= provider.recorded_timeouts[0] <= 4.5
    with pytest.raises(LLMTimeoutError):
        pipe.query("Luật Doanh nghiệp quy định gì?", [], deadline=time.monotonic() + 0.5)


def test_max_waiting_must_be_non_negative_int():
    for bad in (-1, 1.5, None):
        with pytest.raises(ValueError):
            create_app(GatePipe(), max_waiting=bad)
