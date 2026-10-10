"""OpenAI và API tương thích OpenAI."""
from __future__ import annotations
from typing import Optional
from team2_rag.llm.base import LLMProvider, ProviderReply, raise_for_status
from team2_rag.llm.errors import LLMBadOutputError, LLMContentBlockedError
from team2_rag.llm.http import Transport, UrllibTransport
from team2_rag.llm.types import LLMParams, Usage
from team2_rag.prompts.render import RenderedPrompt

class OpenAICompatibleProvider(LLMProvider):
    name = "openai-compatible"
    default_base_url = "https://api.openai.com/v1"
    max_tokens_field = "max_completion_tokens"
    def __init__(self, api_key: str, model: str, timeout_seconds: float = 30.0, *, base_url: Optional[str] = None, transport: Optional[Transport] = None):
        self._api_key, self.model = api_key, model
        self.timeout_seconds = timeout_seconds
        self.base_url = (base_url or self.default_base_url).rstrip("/")
        self.transport = transport or UrllibTransport()
    def build_payload(self, prompt: RenderedPrompt, params: LLMParams) -> dict:
        payload = {"model": self.model, "messages": [{"role": "system", "content": prompt.system}, {"role": "user", "content": prompt.user}], "response_format": {"type": "json_object"}}
        if params.temperature is not None: payload["temperature"] = params.temperature
        if params.max_output_tokens is not None: payload[self.max_tokens_field] = params.max_output_tokens
        return payload
    def complete(self, prompt: RenderedPrompt, params: LLMParams) -> ProviderReply:
        resp = self.transport.post_json(f"{self.base_url}/chat/completions", {"Authorization": f"Bearer {self._api_key}"}, self.build_payload(prompt, params), self.timeout_seconds)
        raise_for_status(self.name, resp.status, resp.json)
        data = resp.json or {}; choices = data.get("choices") or []
        if not choices: raise LLMBadOutputError("Provider không trả về choices.", provider=self.name)
        choice = choices[0]; message = choice.get("message") or {}; finish = choice.get("finish_reason")
        if message.get("refusal") or finish == "content_filter": raise LLMContentBlockedError("Provider từ chối hoặc chặn nội dung.", provider=self.name)
        usage = data.get("usage") or {}
        return ProviderReply(message.get("content") or "", Usage(usage.get("prompt_tokens"), usage.get("completion_tokens")), finish)

class OpenAIProvider(OpenAICompatibleProvider):
    name = "openai"
