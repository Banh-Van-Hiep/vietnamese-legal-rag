"""Deterministic Week10 UI fixture through the real Team2 HTTP adapter; MOCK ONLY.

Query answers are test data, while article lookups use the unchanged Article Store.
No model/index/provider is loaded and no new public API route is introduced.
"""
from __future__ import annotations

import copy
import json
import os
from pathlib import Path
import threading
import time

from team2_rag.api import create_app
from team2_rag.llm.errors import LLMTimeoutError

ROOT = Path(__file__).resolve().parents[2]
DOCUMENT = "luat-59-2020-qh14-v1"
ARTICLE = "dieu-12"


def create_fixture_app():
    rows = []
    with (ROOT / "data/doanh-nghiep/processed/chunks.jsonl").open(encoding="utf-8") as stream:
        for line in stream:
            row = json.loads(line)
            if row.get("document_id") == DOCUMENT and row.get("article_id") == ARTICLE:
                rows.append(row)
    selected = [next(r for r in rows if r["chunk_id"] == f"{DOCUMENT}__{ARTICLE}__k{i}__0") for i in (1, 2)]
    fields = ("chunk_id", "document_id", "article_id", "document_title", "article", "clause", "point", "source_url")
    citations = [{"citation_id": f"C{i}", **{key: row[key] for key in fields}} for i, row in enumerate(selected, 1)]
    attempts = {}
    lock = threading.Lock()

    class FixturePipeline:
        def query(self, question, history=None, *, request_id=None):
            with lock:
                attempt = attempts[question] = attempts.get(question, 0) + 1
                log = os.environ.get("EVALUATION_FIXTURE_LOG")
                if log:
                    with Path(log).open("a", encoding="utf-8") as stream:
                        stream.write(json.dumps({"question": question, "request_id": request_id,
                                                 "attempt": attempt, "mode": "mock"}) + "\n")
            if question.startswith("week10-slow-"):
                time.sleep(4)
            if question.startswith("week10-slow-failed-") or (question.startswith("week10-retry-") and attempt == 1):
                raise LLMTimeoutError("Week10 controlled timeout fixture")
            if question.startswith("week10-insufficient-"):
                return {"status": "insufficient_context", "answer": "Dữ liệu kiểm thử chưa đủ căn cứ để trả lời.", "citations": []}
            response = {"status": "answered", "answer": "Câu trả lời giả lập kiểm thử giao diện [C1]. Nguồn kiểm thử tiếp theo [C2].",
                        "citations": copy.deepcopy(citations)}
            if question.startswith("week10-invalid-"):
                response["answer"] = "Phản hồi kiểm thử không có nhãn nguồn hợp lệ [C9]."
            return response

    app = create_app(pipeline=FixturePipeline())
    app.title = "Week10 UI acceptance fixture — MOCK ONLY"

    @app.middleware("http")
    async def label_mock(request, call_next):
        response = await call_next(request)
        response.headers["X-RAG-Mode"] = "mock"
        return response

    return app
