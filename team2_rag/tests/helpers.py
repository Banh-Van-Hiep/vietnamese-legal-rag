from __future__ import annotations
import json
from pathlib import Path
from team2_rag.config.settings import load_settings
from team2_rag.llm.http import HttpResponse

REPO_ROOT = Path(__file__).resolve().parents[2]
QUESTION = "Người lao động được nghỉ phép hằng năm bao nhiêu ngày?"
CONTEXT = """[C1] chunk_id=LDT_113_01 document_id=BLD2019 article_id=art113 document_title=Bộ luật Lao động 2019 article=Điều 113 clause=Khoản 1 point=null source_url=https://example.com/law\nNgười lao động làm việc đủ 12 tháng được nghỉ hằng năm theo quy định."""


def citation(cid="C1", chunk="LDT_113_01"):
    return {"citation_id": cid, "chunk_id": chunk, "document_id": "BLD2019", "article_id": "art113", "document_title": "Bộ luật Lao động 2019", "article": "Điều 113", "clause": "Khoản 1", "point": None, "source_url": "https://example.com/law"}


def good_output(answer=None):
    return {"status": "answered", "answer": answer or "Người lao động được nghỉ hằng năm theo nguồn [C1].", "citations": [citation()]}

GOOD_TEXT = json.dumps(good_output(), ensure_ascii=False)


def env_for(provider: str, **extra):
    env = {"LLM_PROVIDER": provider, "LLM_MODEL": "test-model", "OPENAI_API_KEY": "test-openai-key", "GEMINI_API_KEY": "test-gemini-key", "QWEN_API_KEY": "test-qwen-key"}
    env.update(extra)
    return env


def settings_for(provider: str, **extra):
    return load_settings(env=env_for(provider, **extra))


class RecordingTransport:
    def __init__(self, *responses):
        self.responses = list(responses)
        self.calls = []
    def post_json(self, url, headers, body, timeout):
        self.calls.append({"url": url, "headers": dict(headers), "body": body, "timeout": timeout})
        return self.responses.pop(0)


def openai_ok(text=GOOD_TEXT, finish="stop"):
    return HttpResponse(200, {"choices": [{"message": {"role": "assistant", "content": text}, "finish_reason": finish}], "usage": {"prompt_tokens": 120, "completion_tokens": 40}})


def gemini_ok(text=GOOD_TEXT, finish="STOP"):
    return HttpResponse(200, {"candidates": [{"content": {"parts": [{"text": text}]}, "finishReason": finish}], "usageMetadata": {"promptTokenCount": 120, "candidatesTokenCount": 40}})
