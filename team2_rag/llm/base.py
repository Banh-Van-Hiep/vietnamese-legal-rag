"""Interface chung của provider. Application KHÔNG import adapter cụ thể, chỉ dùng LLMService."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional

from team2_rag.llm.errors import (
    LLMAuthError,
    LLMConfigError,
    LLMProviderError,
    LLMRateLimitError,
    LLMTimeoutError,
)
from team2_rag.llm.types import LLMParams, Usage
from team2_rag.prompts.render import RenderedPrompt


@dataclass(frozen=True)
class ProviderReply:
    text: str
    usage: Usage
    finish_reason: Optional[str] = None


class LLMProvider(ABC):
    """Một adapter = một provider. Nhận prompt đã render, trả text thô + usage."""

    name: str = ""
    model: str = ""

    @abstractmethod
    def complete(self, prompt: RenderedPrompt, params: LLMParams) -> ProviderReply:
        """Gọi provider một lần. Phải ném lỗi thuộc nhóm `llm.errors`, không ném lỗi riêng của provider."""


def raise_for_status(provider: str, status: int, body: Optional[dict]) -> None:
    """Chuẩn hóa HTTP status thành nhóm lỗi chung. Thông báo chỉ chứa mã trạng thái, không chứa key/prompt."""
    if 200 <= status < 300:
        return
    msg = f"{provider}: HTTP {status}"
    if status in (401, 403):
        raise LLMAuthError(msg + " (xác thực thất bại hoặc không có quyền).", provider=provider, status=status)
    if status == 408:
        raise LLMTimeoutError(msg, provider=provider, status=status)
    if status == 429:
        raise LLMRateLimitError(msg + " (rate limit/quá tải).", provider=provider, status=status)
    if status >= 500:
        raise LLMProviderError(msg, provider=provider, status=status)
    raise LLMConfigError(msg + " (request hoặc model không hợp lệ).", provider=provider, status=status)
