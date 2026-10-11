"""Qwen API adapter; không chạy model local."""
from team2_rag.config.settings import DEFAULT_QWEN_BASE_URL
from team2_rag.llm.openai_client import OpenAICompatibleProvider

class QwenProvider(OpenAICompatibleProvider):
    name = "qwen"
    default_base_url = DEFAULT_QWEN_BASE_URL
    max_tokens_field = "max_tokens"
