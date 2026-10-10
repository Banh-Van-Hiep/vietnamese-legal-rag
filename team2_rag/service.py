"""Python entry point for Team 3; currently always returns mock data."""

from collections.abc import Sequence

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
