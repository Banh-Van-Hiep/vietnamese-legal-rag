"""Configuration for Team 2 LLM clients."""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Mapping, Optional, Union

PROVIDERS = ("openai", "gemini", "qwen", "ollama")
# Ngân sách khởi đầu theo docs/team2_rag/context-builder.md (5 chunk; 3000 token ≈ 9000 ký tự tiếng Việt,
# xấp xỉ vì chưa có tokenizer của LLM).
DEFAULT_MAX_CONTEXT_CHUNKS = 5
DEFAULT_MAX_CONTEXT_CHARS = 9000  # CHỈ dùng khi không có TokenBudget (xấp xỉ, không đáp ứng spec token)
DEFAULT_MAX_CONTEXT_TOKENS = 3000
DEFAULT_SAFETY_MARGIN_TOKENS = 256
DEFAULT_QWEN_BASE_URL = "https://dashscope-intl.aliyuncs.com/compatible-mode/v1"
DEFAULT_OLLAMA_BASE_URL = "http://localhost:11434/v1"  # Ollama OpenAI-compatible API; no API key needed
MAX_TIMEOUT_SECONDS = 30.0  # remote providers
MAX_OLLAMA_TIMEOUT_SECONDS = 600.0  # local inference: model cold start + CPU generation can exceed 30s
_KEY_ENV = {"openai": "OPENAI_API_KEY", "gemini": "GEMINI_API_KEY", "qwen": "QWEN_API_KEY"}


class ConfigError(Exception):
    pass


@dataclass(frozen=True)
class LLMSettings:
    provider: str = "openai"
    model: str = ""
    openai_api_key: str = field(default="", repr=False)
    gemini_api_key: str = field(default="", repr=False)
    qwen_api_key: str = field(default="", repr=False)
    qwen_base_url: str = DEFAULT_QWEN_BASE_URL
    timeout_seconds: float = 30.0
    max_retries: int = 0
    temperature: Optional[float] = 0.0
    max_output_tokens: int = 1500
    max_context_chunks: int = DEFAULT_MAX_CONTEXT_CHUNKS
    max_context_chars: int = DEFAULT_MAX_CONTEXT_CHARS
    max_context_tokens: int = DEFAULT_MAX_CONTEXT_TOKENS
    safety_margin_tokens: int = DEFAULT_SAFETY_MARGIN_TOKENS
    context_window_tokens: Optional[int] = None  # bắt buộc nếu dùng token budget; phụ thuộc model
    ollama_base_url: str = DEFAULT_OLLAMA_BASE_URL  # cuối dataclass để không đổi thứ tự field cũ

    def api_key(self, provider: Optional[str] = None) -> str:
        # ollama chạy cục bộ, không có API key.
        return {"openai": self.openai_api_key, "gemini": self.gemini_api_key, "qwen": self.qwen_api_key, "ollama": ""}[provider or self.provider]

    def params(self):
        from team2_rag.llm.types import LLMParams
        return LLMParams(temperature=self.temperature, max_output_tokens=self.max_output_tokens)

    def validate(self) -> None:
        if self.provider not in PROVIDERS:
            raise ConfigError(f"LLM_PROVIDER không hợp lệ: {self.provider}.")
        if not self.model.strip():
            raise ConfigError("LLM_MODEL chưa được cấu hình.")
        if self.provider != "ollama" and not self.api_key().strip():
            raise ConfigError(f"{_KEY_ENV[self.provider]} chưa được cấu hình.")
        max_timeout = MAX_OLLAMA_TIMEOUT_SECONDS if self.provider == "ollama" else MAX_TIMEOUT_SECONDS
        if self.timeout_seconds <= 0 or self.timeout_seconds > max_timeout:
            raise ConfigError(f"LLM_TIMEOUT_SECONDS phải nằm trong (0, {max_timeout:g}].")
        if self.provider == "ollama":
            if not self.ollama_base_url.startswith(("http://", "https://")):
                raise ConfigError("OLLAMA_BASE_URL phải bắt đầu bằng http:// hoặc https://.")
            # /v1 không cho đặt num_ctx theo request, Ollama cắt prompt im lặng nếu vượt cửa sổ của server:
            # bắt buộc khai báo cửa sổ thật (đặt OLLAMA_CONTEXT_LENGTH trên server cho khớp) để token budget có hiệu lực.
            if self.context_window_tokens is None:
                raise ConfigError("LLM_CONTEXT_WINDOW_TOKENS là bắt buộc khi LLM_PROVIDER=ollama.")
        if self.max_context_chunks <= 0 or self.max_context_chars <= 0:
            raise ConfigError("LLM_MAX_CONTEXT_CHUNKS và LLM_MAX_CONTEXT_CHARS phải lớn hơn 0.")
        if self.max_context_tokens <= 0 or self.safety_margin_tokens <= 0 or (self.context_window_tokens is not None and self.context_window_tokens <= 0):
            raise ConfigError("LLM_MAX_CONTEXT_TOKENS, LLM_SAFETY_MARGIN_TOKENS, LLM_CONTEXT_WINDOW_TOKENS phải lớn hơn 0.")
        if self.context_window_tokens is not None and self.context_window_tokens <= self.max_output_tokens + self.safety_margin_tokens:
            raise ConfigError("LLM_CONTEXT_WINDOW_TOKENS phải lớn hơn LLM_MAX_OUTPUT_TOKENS + LLM_SAFETY_MARGIN_TOKENS.")
        if self.max_retries != 0:
            raise ConfigError("LLM_MAX_RETRIES phải bằng 0 theo mặc định của Team 2.")


def read_dotenv(path: Union[str, Path]) -> dict:
    p = Path(path)
    if not p.is_file():
        return {}
    values = {}
    for raw in p.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        values[key.strip()] = value
    return values


def _num(values: Mapping[str, str], name: str, default, cast):
    raw = values.get(name)
    if raw is None or str(raw).strip() == "":
        return default
    try:
        return cast(str(raw).strip())
    except ValueError:
        raise ConfigError(f"{name} không phải số hợp lệ.") from None


def load_settings(env: Optional[Mapping[str, str]] = None, dotenv_path: Optional[Union[str, Path]] = None) -> LLMSettings:
    values = {}
    path = dotenv_path if dotenv_path else (".env" if env is None else None)
    if path:
        values.update(read_dotenv(path))
    values.update(os.environ if env is None else env)
    d = LLMSettings()
    temp = _num(values, "LLM_TEMPERATURE", d.temperature, float)
    return LLMSettings(
        provider=str(values.get("LLM_PROVIDER", d.provider)).strip().lower() or d.provider,
        model=str(values.get("LLM_MODEL", "")).strip(),
        openai_api_key=str(values.get("OPENAI_API_KEY", "")).strip(),
        gemini_api_key=str(values.get("GEMINI_API_KEY", "")).strip(),
        qwen_api_key=str(values.get("QWEN_API_KEY", "")).strip(),
        qwen_base_url=str(values.get("QWEN_BASE_URL", d.qwen_base_url)).strip() or d.qwen_base_url,
        timeout_seconds=_num(values, "LLM_TIMEOUT_SECONDS", d.timeout_seconds, float),
        max_retries=_num(values, "LLM_MAX_RETRIES", d.max_retries, int),
        temperature=temp,
        max_output_tokens=_num(values, "LLM_MAX_OUTPUT_TOKENS", d.max_output_tokens, int),
        max_context_chunks=_num(values, "LLM_MAX_CONTEXT_CHUNKS", d.max_context_chunks, int),
        max_context_chars=_num(values, "LLM_MAX_CONTEXT_CHARS", d.max_context_chars, int),
        max_context_tokens=_num(values, "LLM_MAX_CONTEXT_TOKENS", d.max_context_tokens, int),
        safety_margin_tokens=_num(values, "LLM_SAFETY_MARGIN_TOKENS", d.safety_margin_tokens, int),
        context_window_tokens=_num(values, "LLM_CONTEXT_WINDOW_TOKENS", d.context_window_tokens, int),
        ollama_base_url=str(values.get("OLLAMA_BASE_URL", d.ollama_base_url)).strip() or d.ollama_base_url,
    )
