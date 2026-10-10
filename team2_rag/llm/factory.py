"""Chọn provider bằng cấu hình. Thêm provider mới = thêm adapter + 1 dòng trong _REGISTRY."""
from __future__ import annotations

from typing import Callable, Optional

from team2_rag.config.settings import ConfigError, LLMSettings, load_settings
from team2_rag.llm.base import LLMProvider
from team2_rag.llm.gemini_client import GeminiProvider
from team2_rag.llm.http import Transport
from team2_rag.llm.openai_client import OpenAIProvider
from team2_rag.llm.qwen_client import QwenProvider
from team2_rag.llm.service import LLMService


def _openai(s: LLMSettings, t: Optional[Transport]) -> LLMProvider:
    return OpenAIProvider(s.openai_api_key, s.model, s.timeout_seconds, transport=t)


def _gemini(s: LLMSettings, t: Optional[Transport]) -> LLMProvider:
    return GeminiProvider(s.gemini_api_key, s.model, s.timeout_seconds, transport=t)


def _qwen(s: LLMSettings, t: Optional[Transport]) -> LLMProvider:
    return QwenProvider(s.qwen_api_key, s.model, s.timeout_seconds, base_url=s.qwen_base_url, transport=t)


_REGISTRY = {"openai": _openai, "gemini": _gemini, "qwen": _qwen}


def create_provider(settings: LLMSettings, transport: Optional[Transport] = None) -> LLMProvider:
    settings.validate()  # fail nhanh: thiếu model/key thì báo ngay, thông báo không chứa giá trị key
    try:
        return _REGISTRY[settings.provider](settings, transport)
    except KeyError:  # pragma: no cover - validate() đã chặn
        raise ConfigError(f"Provider '{settings.provider}' chưa được hỗ trợ.") from None


def create_llm_service(
    settings: Optional[LLMSettings] = None,
    *,
    transport: Optional[Transport] = None,
    **service_kwargs,
) -> LLMService:
    """Tạo LLMService từ cấu hình (mặc định đọc os.environ và ./.env)."""
    settings = settings or load_settings()
    provider = create_provider(settings, transport)
    return LLMService(provider, max_retries=settings.max_retries, default_params=settings.params(), **service_kwargs)
