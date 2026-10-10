"""Configuration for Team 2 LLM clients."""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Mapping, Optional, Union

PROVIDERS = ("openai", "gemini", "qwen")
DEFAULT_QWEN_BASE_URL = "https://dashscope-intl.aliyuncs.com/compatible-mode/v1"
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

    def api_key(self, provider: Optional[str] = None) -> str:
        return {"openai": self.openai_api_key, "gemini": self.gemini_api_key, "qwen": self.qwen_api_key}[provider or self.provider]

    def params(self):
        from team2_rag.llm.types import LLMParams
        return LLMParams(temperature=self.temperature, max_output_tokens=self.max_output_tokens)

    def validate(self) -> None:
        if self.provider not in PROVIDERS:
            raise ConfigError(f"LLM_PROVIDER không hợp lệ: {self.provider}.")
        if not self.model.strip():
            raise ConfigError("LLM_MODEL chưa được cấu hình.")
        if not self.api_key().strip():
            raise ConfigError(f"{_KEY_ENV[self.provider]} chưa được cấu hình.")
        if self.timeout_seconds <= 0 or self.timeout_seconds > 30:
            raise ConfigError("LLM_TIMEOUT_SECONDS phải nằm trong (0, 30].")
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
    )
