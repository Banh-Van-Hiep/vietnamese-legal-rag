import pytest
from pydantic import ValidationError

from team2_rag.config.llm_config import LLMClientSettings
from team2_rag.config.settings import ConfigError, LLMSettings

_ENV = [
    "LLM_PROVIDER", "LLM_MODEL", "OPENAI_API_KEY", "GEMINI_API_KEY", "QWEN_API_KEY", "QWEN_BASE_URL",
    "LLM_TIMEOUT_SECONDS", "LLM_MAX_RETRIES", "LLM_TEMPERATURE", "LLM_MAX_OUTPUT_TOKENS", "LLM_MAX_TOKENS",
    "LLM_CONTEXT_WINDOW_TOKENS", "LLM_MAX_CONTEXT_TOKENS", "LLM_SAFETY_MARGIN_TOKENS",
    "LLM_MAX_CONTEXT_CHUNKS", "LLM_MAX_CONTEXT_CHARS", "OLLAMA_BASE_URL",
]


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch):
    for k in _ENV:
        monkeypatch.delenv(k, raising=False)


def load(**env):
    return LLMClientSettings(_env_file=None, **env)


def test_defaults():
    s = load()
    assert (s.provider, s.timeout_seconds, s.max_retries, s.max_tokens) == ("openai", 30.0, 0, 1500)
    assert (s.max_context_chunks, s.max_context_tokens, s.safety_margin_tokens) == (5, 3000, 256)
    assert s.context_window_tokens is None


def test_env_overrides(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", " Gemini ")
    monkeypatch.setenv("LLM_MODEL", "g-model")
    monkeypatch.setenv("LLM_MAX_OUTPUT_TOKENS", "800")
    monkeypatch.setenv("LLM_CONTEXT_WINDOW_TOKENS", "32000")
    s = load()
    assert (s.provider, s.model, s.max_tokens, s.context_window_tokens) == ("gemini", "g-model", 800, 32000)


def test_api_keys_are_stripped(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "  k-openai\n")
    monkeypatch.setenv("QWEN_API_KEY", "k-qwen \n")
    s = load()
    assert s.api_key("openai") == "k-openai" and s.api_key("qwen") == "k-qwen"
    assert s.to_legacy().openai_api_key == "k-openai"


def test_max_tokens_alias(monkeypatch):
    monkeypatch.setenv("LLM_MAX_TOKENS", "700")
    assert load().max_tokens == 700


def test_secret_not_in_repr(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "super-secret")
    s = load()
    assert "super-secret" not in repr(s) and "super-secret" not in str(s)
    assert s.api_key("openai") == "super-secret"


@pytest.mark.parametrize(
    "name,value",
    [("LLM_PROVIDER", "claude"), ("LLM_TIMEOUT_SECONDS", "31"), ("LLM_TIMEOUT_SECONDS", "0"), ("LLM_MAX_RETRIES", "1")],
)
def test_invalid_values_rejected(monkeypatch, name, value):
    monkeypatch.setenv(name, value)
    with pytest.raises(ValidationError):
        load()


def test_window_must_exceed_output_plus_margin(monkeypatch):
    monkeypatch.setenv("LLM_CONTEXT_WINDOW_TOKENS", "1500")
    with pytest.raises(ValidationError):
        load()


def test_validate_runtime_requires_model_and_key(monkeypatch):
    with pytest.raises(ConfigError):
        load().validate_runtime()
    monkeypatch.setenv("LLM_MODEL", "m")
    with pytest.raises(ConfigError):
        load().validate_runtime()
    monkeypatch.setenv("OPENAI_API_KEY", "k")
    assert load().validate_runtime().model == "m"


def test_to_legacy_roundtrip(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "qwen")
    monkeypatch.setenv("LLM_MODEL", "qwen-max")
    monkeypatch.setenv("QWEN_API_KEY", "k")
    monkeypatch.setenv("LLM_MAX_OUTPUT_TOKENS", "900")
    monkeypatch.setenv("LLM_CONTEXT_WINDOW_TOKENS", "32000")
    legacy = load().to_legacy()
    assert isinstance(legacy, LLMSettings)
    assert (legacy.provider, legacy.model, legacy.max_output_tokens, legacy.context_window_tokens) == (
        "qwen", "qwen-max", 900, 32000,
    )
    legacy.validate()


def test_to_legacy_matches_runtime_loader(monkeypatch):
    """LLMClientSettings must stay equivalent to `load_settings` (the loader runtime/factory/answer actually use)."""
    from team2_rag.config.settings import load_settings
    env = {
        "LLM_PROVIDER": "qwen", "LLM_MODEL": "qwen-plus", "QWEN_API_KEY": " k-qwen \n", "LLM_MAX_OUTPUT_TOKENS": "800",
        "LLM_CONTEXT_WINDOW_TOKENS": "32000", "LLM_TEMPERATURE": "0.2", "LLM_MAX_CONTEXT_CHUNKS": "4",
    }
    for k, v in env.items():
        monkeypatch.setenv(k, v)
    assert load().to_legacy() == load_settings(env=env)


def test_both_loaders_reject_window_that_cannot_hold_output_and_margin():
    from team2_rag.config.settings import load_settings
    env = {"LLM_PROVIDER": "gemini", "LLM_MODEL": "m", "GEMINI_API_KEY": "k", "LLM_CONTEXT_WINDOW_TOKENS": "1756"}
    with pytest.raises(ConfigError):
        load_settings(env=env).validate()
    with pytest.raises(ValidationError):
        load(**env)


# --- ollama (local, keyless) -------------------------------------------------------------------------------------
_OLLAMA_ENV = {"LLM_PROVIDER": "ollama", "LLM_MODEL": "qwen2.5:3b", "LLM_CONTEXT_WINDOW_TOKENS": "8192"}


def test_ollama_needs_no_key_but_needs_model_and_window(monkeypatch):
    for k, v in _OLLAMA_ENV.items():
        monkeypatch.setenv(k, v)
    s = load()
    assert s.api_key() == "" and s.ollama_base_url == "http://localhost:11434/v1"
    assert s.validate_runtime().model == "qwen2.5:3b"
    monkeypatch.delenv("LLM_CONTEXT_WINDOW_TOKENS")
    with pytest.raises(ConfigError):
        load().validate_runtime()


def test_ollama_timeout_limit_is_600_others_stay_30(monkeypatch):
    for k, v in _OLLAMA_ENV.items():
        monkeypatch.setenv(k, v)
    monkeypatch.setenv("LLM_TIMEOUT_SECONDS", "120")
    assert load().timeout_seconds == 120.0
    monkeypatch.setenv("LLM_TIMEOUT_SECONDS", "601")
    with pytest.raises(ValidationError):
        load()
    monkeypatch.setenv("LLM_PROVIDER", "openai")
    monkeypatch.setenv("LLM_TIMEOUT_SECONDS", "120")
    with pytest.raises(ValidationError):
        load()


def test_ollama_to_legacy_matches_runtime_loader(monkeypatch):
    from team2_rag.config.settings import load_settings
    env = {**_OLLAMA_ENV, "OLLAMA_BASE_URL": " http://127.0.0.1:9999/v1 ", "LLM_TIMEOUT_SECONDS": "120", "LLM_TEMPERATURE": "0.1"}
    for k, v in env.items():
        monkeypatch.setenv(k, v)
    legacy = load().to_legacy()
    assert legacy == load_settings(env=env)
    assert legacy.ollama_base_url == "http://127.0.0.1:9999/v1"
    legacy.validate()
