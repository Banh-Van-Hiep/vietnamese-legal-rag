"""Fake provider cho offline testing, không cần API key hay mạng."""
from __future__ import annotations
import json
from typing import List, Sequence, Union
from team2_rag.llm.base import LLMProvider, ProviderReply
from team2_rag.llm.types import LLMParams, Usage
from team2_rag.prompts.render import RenderedPrompt

class FakeLLMProvider(LLMProvider):
    name = "fake"
    def __init__(self, responses: Sequence[Union[str, dict, Exception]] = (), model: str = "fake-model"):
        self.model = model
        self._responses: List[Union[str, dict, Exception]] = list(responses)
        self.calls = []
    def complete(self, prompt: RenderedPrompt, params: LLMParams) -> ProviderReply:
        self.calls.append((prompt, params))
        if not self._responses:
            raise AssertionError("FakeLLMProvider hết phản hồi định sẵn.")
        item = self._responses.pop(0)
        if isinstance(item, Exception):
            raise item
        text = item if isinstance(item, str) else json.dumps(item, ensure_ascii=False)
        return ProviderReply(text=text, usage=Usage(10, 5), finish_reason="stop")
