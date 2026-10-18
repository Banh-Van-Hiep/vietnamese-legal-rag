"""Token budget cho legal context (docs/team2_rag/context-builder.md).

Spec: đếm bằng tokenizer của LLM đang dùng, trên prompt đã serialize;
budget = min(3000, context_window - token(system/question/history) - output_reserve - margin).
Module này chỉ định nghĩa giao diện và công thức; counter phải khớp provider/model thật.
Không có counter "đoán" cho model chưa hỗ trợ: gọi `token_budget_from_settings` với provider chưa có
counter sẽ báo lỗi cấu hình thay vì trả về ước lượng.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from team2_rag.config.settings import ConfigError, LLMSettings
from team2_rag.llm.errors import LLMConfigError


@runtime_checkable
class TokenCounter(Protocol):
    def count(self, text: str) -> int:
        """Số token của `text` theo tokenizer của đúng model sẽ nhận prompt."""


class TiktokenCounter:
    """Counter cho model OpenAI (ví dụ gpt-4o -> o200k_base) qua thư viện `tiktoken` (dependency tùy chọn)."""

    def __init__(self, model: str):
        try:
            import tiktoken
        except ImportError:
            raise LLMConfigError("Cần cài `tiktoken` để đếm token cho provider openai (pip install tiktoken).",
                                 provider="openai") from None
        try:
            self._encoding = tiktoken.encoding_for_model(model)
        except KeyError:
            raise LLMConfigError(f"tiktoken không nhận ra model '{model}'; không đoán tokenizer.", provider="openai") from None
        self.model = model

    def count(self, text: str) -> int:
        return len(self._encoding.encode(text, disallowed_special=()))


@dataclass(frozen=True)
class TokenBudget:
    counter: TokenCounter
    context_window_tokens: int
    max_context_tokens: int = 3000
    output_reserve_tokens: int = 1500
    safety_margin_tokens: int = 256

    def __post_init__(self):
        for name in ("context_window_tokens", "max_context_tokens", "output_reserve_tokens", "safety_margin_tokens"):
            if getattr(self, name) <= 0:
                raise ValueError(f"{name} phải > 0")

    @property
    def prompt_limit(self) -> int:
        """Tổng token tối đa của prompt (system + user) gửi đi."""
        return self.context_window_tokens - self.output_reserve_tokens - self.safety_margin_tokens

    def available_for_context(self, fixed_prompt_tokens: int) -> int:
        """min(max_context, window - fixed - output_reserve - margin); <= 0 nghĩa là không còn chỗ cho nguồn."""
        return min(self.max_context_tokens, self.prompt_limit - fixed_prompt_tokens)


def token_budget_from_settings(settings: LLMSettings) -> TokenBudget:
    """Dựng TokenBudget từ cấu hình; thiếu thông tin hoặc provider chưa có counter thì báo lỗi, không ước lượng."""
    if settings.context_window_tokens is None:
        raise ConfigError("LLM_CONTEXT_WINDOW_TOKENS chưa được cấu hình (cần context window của đúng model).")
    if settings.provider == "openai":
        counter: TokenCounter = TiktokenCounter(settings.model)
    else:
        raise ConfigError(
            f"Chưa có token counter cho provider '{settings.provider}'. Gemini cần API countTokens, "
            "Qwen cần tokenizer của đúng checkpoint; hãy truyền TokenCounter riêng vào TokenBudget.")
    return TokenBudget(counter, settings.context_window_tokens, settings.max_context_tokens,
                       settings.max_output_tokens, settings.safety_margin_tokens)
