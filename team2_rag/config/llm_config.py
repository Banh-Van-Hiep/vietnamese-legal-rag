from __future__ import annotations

from functools import lru_cache
from typing import Literal, Optional

from pydantic import AliasChoices, Field, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from team2_rag.config.settings import (
    DEFAULT_MAX_CONTEXT_CHARS,
    DEFAULT_MAX_CONTEXT_CHUNKS,
    DEFAULT_MAX_CONTEXT_TOKENS,
    DEFAULT_OLLAMA_BASE_URL,
    DEFAULT_QWEN_BASE_URL,
    DEFAULT_SAFETY_MARGIN_TOKENS,
    MAX_OLLAMA_TIMEOUT_SECONDS,
    MAX_TIMEOUT_SECONDS,
    ConfigError,
    LLMSettings,
)

Provider = Literal["openai", "gemini", "qwen", "ollama"]
_KEY_ENV = {"openai": "OPENAI_API_KEY", "gemini": "GEMINI_API_KEY", "qwen": "QWEN_API_KEY"}


class LLMClientSettings(BaseSettings):
    """Typed/validated front-end for the same environment variables.

    Runtime authority is `settings.LLMSettings` (`load_settings`), which is what `runtime.py`, `factory.py` and
    `answer.py` consume. This class must stay equivalent: `to_legacy()` is pinned to `load_settings` by
    `tests/test_llm_config.py::test_to_legacy_matches_runtime_loader`.
    """
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
        env_ignore_empty=True,
        frozen=True,
    )

    provider: Provider = Field("openai", validation_alias="LLM_PROVIDER")
    model: str = Field("", validation_alias="LLM_MODEL")
    openai_api_key: SecretStr = Field(SecretStr(""), validation_alias="OPENAI_API_KEY")
    gemini_api_key: SecretStr = Field(SecretStr(""), validation_alias="GEMINI_API_KEY")
    qwen_api_key: SecretStr = Field(SecretStr(""), validation_alias="QWEN_API_KEY")
    qwen_base_url: str = Field(DEFAULT_QWEN_BASE_URL, validation_alias="QWEN_BASE_URL")
    ollama_base_url: str = Field(DEFAULT_OLLAMA_BASE_URL, validation_alias="OLLAMA_BASE_URL")

    # Field ceiling is the largest any provider may use; the stricter 30s limit for remote providers is enforced below.
    timeout_seconds: float = Field(30.0, gt=0, le=MAX_OLLAMA_TIMEOUT_SECONDS, validation_alias="LLM_TIMEOUT_SECONDS")
    max_retries: int = Field(0, ge=0, le=0, validation_alias="LLM_MAX_RETRIES")
    temperature: Optional[float] = Field(0.0, ge=0.0, le=2.0, validation_alias="LLM_TEMPERATURE")
    max_tokens: int = Field(
        1500, gt=0, validation_alias=AliasChoices("LLM_MAX_OUTPUT_TOKENS", "LLM_MAX_TOKENS")
    )
    context_window_tokens: Optional[int] = Field(
        None, gt=0, validation_alias="LLM_CONTEXT_WINDOW_TOKENS"
    )
    max_context_tokens: int = Field(
        DEFAULT_MAX_CONTEXT_TOKENS, gt=0, validation_alias="LLM_MAX_CONTEXT_TOKENS"
    )
    safety_margin_tokens: int = Field(
        DEFAULT_SAFETY_MARGIN_TOKENS, gt=0, validation_alias="LLM_SAFETY_MARGIN_TOKENS"
    )
    max_context_chunks: int = Field(
        DEFAULT_MAX_CONTEXT_CHUNKS, ge=1, validation_alias="LLM_MAX_CONTEXT_CHUNKS"
    )
    max_context_chars: int = Field(
        DEFAULT_MAX_CONTEXT_CHARS, ge=1, validation_alias="LLM_MAX_CONTEXT_CHARS"
    )

    @field_validator("provider", mode="before")
    @classmethod
    def _norm_provider(cls, v):
        return v.strip().lower() if isinstance(v, str) else v

    @field_validator("model", "qwen_base_url", "ollama_base_url", mode="before")
    @classmethod
    def _strip(cls, v):
        return v.strip() if isinstance(v, str) else v

    @field_validator("openai_api_key", "gemini_api_key", "qwen_api_key", mode="before")
    @classmethod
    def _strip_key(cls, v):
        # load_settings() strips keys; a stray newline/space (e.g. from a secrets file) would otherwise
        # reach the Authorization header and break every provider call.
        if isinstance(v, SecretStr):
            return SecretStr(v.get_secret_value().strip())
        return v.strip() if isinstance(v, str) else v

    @model_validator(mode="after")
    def _timeout_within_provider_limit(self) -> "LLMClientSettings":
        if self.provider != "ollama" and self.timeout_seconds > MAX_TIMEOUT_SECONDS:
            raise ValueError("LLM_TIMEOUT_SECONDS phải nằm trong (0, 30] (trừ provider ollama).")
        return self

    @model_validator(mode="after")
    def _window_fits_output(self) -> "LLMClientSettings":
        if (
            self.context_window_tokens is not None
            and self.context_window_tokens <= self.max_tokens + self.safety_margin_tokens
        ):
            raise ValueError("LLM_CONTEXT_WINDOW_TOKENS phải lớn hơn max_tokens + safety_margin_tokens.")
        return self

    def api_key(self, provider: Optional[str] = None) -> str:
        p = provider or self.provider
        return {
            "openai": self.openai_api_key,
            "gemini": self.gemini_api_key,
            "qwen": self.qwen_api_key,
            "ollama": SecretStr(""),  # local, keyless
        }[p].get_secret_value()

    def validate_runtime(self) -> "LLMClientSettings":
        if not self.model:
            raise ConfigError("LLM_MODEL chưa được cấu hình.")
        if self.provider != "ollama" and not self.api_key().strip():
            raise ConfigError(f"{_KEY_ENV[self.provider]} chưa được cấu hình.")
        if self.provider == "ollama" and self.context_window_tokens is None:
            raise ConfigError("LLM_CONTEXT_WINDOW_TOKENS là bắt buộc khi LLM_PROVIDER=ollama.")
        return self

    def to_legacy(self) -> LLMSettings:
        """Adapter cho llm.factory.create_llm_service / answer.generate_answer."""
        return LLMSettings(
            provider=self.provider,
            model=self.model,
            openai_api_key=self.openai_api_key.get_secret_value(),
            gemini_api_key=self.gemini_api_key.get_secret_value(),
            qwen_api_key=self.qwen_api_key.get_secret_value(),
            qwen_base_url=self.qwen_base_url,
            timeout_seconds=self.timeout_seconds,
            max_retries=self.max_retries,
            temperature=self.temperature,
            max_output_tokens=self.max_tokens,
            max_context_chunks=self.max_context_chunks,
            max_context_chars=self.max_context_chars,
            max_context_tokens=self.max_context_tokens,
            safety_margin_tokens=self.safety_margin_tokens,
            context_window_tokens=self.context_window_tokens,
            ollama_base_url=self.ollama_base_url,
        )


@lru_cache(maxsize=1)
def get_llm_settings() -> LLMClientSettings:
    return LLMClientSettings()
