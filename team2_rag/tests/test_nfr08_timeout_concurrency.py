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
        def query(self, q, h, request_id=None):
            started.set()
            release.wait(5.0)
            return {"status": "insufficient_context", "answer": "Chưa đủ căn cứ.", "citations": []}

    app = create_app(BlockingPipe(), timeout_seconds=0.1)
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
