"""Python entry point for Team 3; currently always returns mock data."""

from collections.abc import Sequence

from typing import Any, Mapping, Optional

from .answer import answer_from_rerank
from .config.settings import LLMSettings, load_settings
from .llm.errors import LLMError
from .llm.factory import create_llm_service
from .llm.service import LLMService
from .llm.tokens import TokenBudget, token_budget_from_settings
from .mock import MockScenario, make_mock_response
from .types import HistoryMessage, RAGResponse


def query(
    question: str,
    history: Sequence[HistoryMessage] | None = None,
    *,
    scenario: MockScenario = "answered",
) -> RAGResponse:
    """Accept the internal question/history shape, without retrieval or LLM calls.

    History is accepted for integration but not interpreted by the mock.
    Team 3 retains API request validation, HTTP and public response fields.
    The scenario keyword is a test helper, not a new API request field.
    """
    if not isinstance(question, str) or not question.strip():
        raise ValueError("question must be a non-empty string")
    if len(question.strip()) > 2000:
        raise ValueError("question must not exceed 2000 characters after trimming")
    return make_mock_response(scenario)


def generate_answer(
    rerank_output: Mapping[str, Any],
    history: Optional[Sequence[HistoryMessage]] = None,
    *,
    llm_service: Optional[LLMService] = None,
    settings: Optional[LLMSettings] = None,
    token_budget: Optional[TokenBudget] = None,
    request_id: Optional[str] = None,
) -> RAGResponse:
    """Luồng thật của VLRA-29: output Reranker -> context -> LLM -> RAGResponse đã kiểm tra citation.

    Gọi LLM thật theo cấu hình (LLM_PROVIDER/LLM_MODEL/*_API_KEY) khi không truyền `llm_service`; test truyền
    FakeLLMProvider qua `llm_service`. Nếu cấu hình có LLM_CONTEXT_WINDOW_TOKENS thì dùng token budget, ngược lại
    dùng budget ký tự xấp xỉ (chưa đáp ứng spec token). Lỗi được raise nguyên dạng (xem `to_error_response`).
    `query()` ở trên vẫn là mock cho Team 3 cho tới khi có retrieval + reranker thật.
    """
    if llm_service is None:
        settings = settings or load_settings()
        llm_service = create_llm_service(settings)
        if token_budget is None and settings.context_window_tokens is not None:
            token_budget = token_budget_from_settings(settings)
    limits = {} if settings is None else {"max_chunks": settings.max_context_chunks, "max_context_chars": settings.max_context_chars}
    return answer_from_rerank(rerank_output, llm_service, history, token_budget=token_budget, request_id=request_id, **limits)


_ERROR_MESSAGES = {
    "LLM_TIMEOUT": ("Dịch vụ tạm thời không phản hồi.", True),
    "LLM_UNAVAILABLE": ("Dịch vụ xử lý tạm thời không khả dụng.", True),
    "INVALID_LLM_OUTPUT": ("Phản hồi từ dịch vụ xử lý không hợp lệ.", False),
    "CITATION_INVALID": ("Phản hồi từ dịch vụ xử lý không hợp lệ.", False),
}


def to_error_response(exc: BaseException) -> Optional[dict]:
    """ErrorResponse {"error": {code, message, retryable}} cho lỗi LLM; None nếu không phải LLMError.

    `retryable` theo bảng lỗi trong docs/team2_rag/rag-io-specification.md (timeout/unavailable có thể retry; output
    hoặc citation sai thì không). Message an toàn: không chứa lỗi thô của provider, prompt hay API key.
    ValueError/ContextBuildError/ContextBudgetError (input nội bộ sai) trả None: tầng API quyết định HTTP 400/500.
    """
    if not isinstance(exc, LLMError):
        return None
    message, retryable = _ERROR_MESSAGES.get(exc.error_code, _ERROR_MESSAGES["LLM_UNAVAILABLE"])
    return {"error": {"code": exc.error_code, "message": message, "retryable": retryable}}
