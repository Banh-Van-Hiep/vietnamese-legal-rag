"""Ollama (local, free) qua API tương thích OpenAI `/v1/chat/completions`.

Đã đối chiếu tài liệu Ollama (docs.ollama.com/openai): `/v1/chat/completions` hỗ trợ `response_format` (JSON mode),
`max_tokens`, `temperature`; `max_completion_tokens` KHÔNG nằm trong danh sách hỗ trợ nên không dùng (khác OpenAI).
API key "required but ignored" -> gửi placeholder, không cần key trả phí. `/v1` không nhận `num_ctx`: cửa sổ context
do server quyết định (OLLAMA_CONTEXT_LENGTH hoặc Modelfile) và phải khớp LLM_CONTEXT_WINDOW_TOKENS.
"""
from __future__ import annotations

from typing import Optional

from team2_rag.config.settings import DEFAULT_OLLAMA_BASE_URL
from team2_rag.llm.base import ProviderReply, raise_for_status
from team2_rag.llm.errors import LLMBadOutputError, LLMConfigError, LLMContentBlockedError
from team2_rag.llm.http import Transport
from team2_rag.llm.openai_client import OpenAICompatibleProvider
from team2_rag.llm.types import LLMParams, Usage
from team2_rag.prompts.render import RenderedPrompt

_PLACEHOLDER_KEY = "ollama"  # Ollama bỏ qua giá trị này; không phải secret.


def _count(value) -> Optional[int]:
    return value if type(value) is int and value >= 0 else None


class OllamaProvider(OpenAICompatibleProvider):
    name = "ollama"
    default_base_url = DEFAULT_OLLAMA_BASE_URL
    max_tokens_field = "max_tokens"

    def __init__(self, model: str, timeout_seconds: float = 120.0, *, base_url: Optional[str] = None,
                 transport: Optional[Transport] = None):
        super().__init__(_PLACEHOLDER_KEY, model, timeout_seconds, base_url=base_url, transport=transport)

    def complete(self, prompt: RenderedPrompt, params: LLMParams) -> ProviderReply:
        resp = self.transport.post_json(f"{self.base_url}/chat/completions", {"Authorization": f"Bearer {self._api_key}"},
                                        self.build_payload(prompt, params), self.timeout_seconds)
        if resp.status == 404:  # model chưa pull, hoặc base URL thiếu /v1
            raise LLMConfigError(
                f"ollama: HTTP 404 - model '{self.model}' chưa có (chạy `ollama pull {self.model}`) hoặc OLLAMA_BASE_URL sai.",
                provider=self.name, status=404)
        raise_for_status(self.name, resp.status, resp.json)
        data = resp.json
        if not isinstance(data, dict):
            raise LLMBadOutputError("Ollama trả về phản hồi không phải JSON object.", provider=self.name, raw_text=(resp.text or "")[:200])
        choices = data.get("choices")
        if not isinstance(choices, list) or not choices or not isinstance(choices[0], dict):
            raise LLMBadOutputError("Ollama không trả về choices hợp lệ.", provider=self.name)
        choice = choices[0]
        message = choice.get("message")
        if not isinstance(message, dict):
            raise LLMBadOutputError("Ollama trả về choices[0].message không hợp lệ.", provider=self.name)
        finish = choice.get("finish_reason")
        if finish == "content_filter" or message.get("refusal"):
            raise LLMContentBlockedError("Provider từ chối hoặc chặn nội dung.", provider=self.name)
        content = message.get("content")
        if content is not None and not isinstance(content, str):
            raise LLMBadOutputError("Ollama trả về message.content không phải chuỗi.", provider=self.name)
        usage = data.get("usage") if isinstance(data.get("usage"), dict) else {}
        return ProviderReply(content or "", Usage(_count(usage.get("prompt_tokens")), _count(usage.get("completion_tokens"))), finish)
