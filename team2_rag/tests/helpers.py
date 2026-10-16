from __future__ import annotations
import json
from pathlib import Path
from team2_rag.config.settings import load_settings
from team2_rag.llm.http import HttpResponse

REPO_ROOT = Path(__file__).resolve().parents[2]
QUESTION = "Luật Doanh nghiệp quy định về những vấn đề gì?"
CONTEXT = """[C1] chunk_id=luat-59-2020-qh14-v1__dieu-1__k0__0 document_id=luat-59-2020-qh14-v1 article_id=dieu-1 document_title=Luật Doanh nghiệp article=Điều 1 clause=null point=null source_url=https://vbpl.vn/boyte/Pages/vbpq-toanvan.aspx?ItemID=142881
Luật này quy định về việc thành lập, tổ chức quản lý, tổ chức lại, giải thể và hoạt động có liên quan của doanh nghiệp."""


def citation(cid="C1", chunk="luat-59-2020-qh14-v1__dieu-1__k0__0"):
    return {"citation_id": cid, "chunk_id": chunk, "document_id": "luat-59-2020-qh14-v1", "article_id": "dieu-1", "document_title": "Luật Doanh nghiệp", "article": "Điều 1", "clause": None, "point": None, "source_url": "https://vbpl.vn/boyte/Pages/vbpq-toanvan.aspx?ItemID=142881"}


def good_output(answer=None):
    return {"status": "answered", "answer": answer or "Luật Doanh nghiệp quy định về thành lập, tổ chức quản lý và hoạt động của doanh nghiệp [C1].", "citations": [citation()]}

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
