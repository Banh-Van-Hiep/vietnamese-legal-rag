"""Token budget cho legal context (docs/team2_rag/context-builder.md).

Spec: đếm bằng tokenizer của LLM đang dùng, trên prompt đã serialize;
budget = min(3000, context_window - token(system/question/history) - output_reserve - margin).
Module này chỉ định nghĩa giao diện và công thức; counter phải khớp provider/model thật.
OpenAI dùng tiktoken (chính xác). Gemini/Qwen chưa có counter chính xác trong repo: `token_budget_from_settings`
dùng `ConservativeByteCounter` - CHẶN TRÊN (1 token <= 1 byte UTF-8), luôn đếm dư chứ không đếm thiếu, nên prompt
không vượt context window; đổi lại context nguồn bị cắt sớm hơn (tiếng Việt ~2-3 byte/ký tự). Muốn tận dụng
cửa sổ tối đa, truyền `TokenCounter` chính xác của provider vào `TokenBudget`.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from team2_rag.config.settings import ConfigError, LLMSettings
from team2_rag.llm.errors import LLMConfigError

logger = logging.getLogger("team2_rag.tokens")


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


class ConservativeByteCounter:
    """Chặn trên số token cho tokenizer chưa có counter chính xác (Gemini, Qwen).

    Mỗi token của tokenizer byte-level/SentencePiece phủ >= 1 byte đầu vào nên `len(utf-8)` không bao giờ nhỏ hơn
    số token thật; token đặc biệt/chat template do `safety_margin_tokens` hấp thụ. Đây là chặn trên có chứng minh,
    không phải ước lượng: sai số chỉ theo hướng dư (cắt context sớm), không bao giờ vượt giới hạn.
    """

    exact = False

    def count(self, text: str) -> int:
        return len(text.encode("utf-8"))


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
    """Dựng TokenBudget từ cấu hình. Thiếu LLM_CONTEXT_WINDOW_TOKENS hoặc tiktoken/model OpenAI sai -> lỗi cấu hình.

    Provider không phải OpenAI dùng `ConservativeByteCounter` (chặn trên, có log cảnh báo) thay vì từ chối khởi động.
    """
    if settings.context_window_tokens is None:
        raise ConfigError("LLM_CONTEXT_WINDOW_TOKENS chưa được cấu hình (cần context window của đúng model).")
    if settings.provider == "openai":
        counter: TokenCounter = TiktokenCounter(settings.model)
    else:
        logger.warning(
            "token_counter_fallback provider=%s: dùng chặn trên theo byte UTF-8 (không chính xác, luôn đếm dư); "
            "cung cấp TokenCounter của provider để dùng hết context window.", settings.provider)
        counter = ConservativeByteCounter()
    return TokenBudget(counter, settings.context_window_tokens, settings.max_context_tokens,
                       settings.max_output_tokens, settings.safety_margin_tokens)
