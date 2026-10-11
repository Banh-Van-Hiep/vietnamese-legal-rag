"""Build LLM input without selecting or modifying retrieved chunks."""
from __future__ import annotations

from typing import Iterable, Mapping, Optional, Union

from team2_rag.llm.types import HistoryTurn, LLMInput, LLMParams
from team2_rag.prompts.templates import OUTPUT_INSTRUCTION, PROMPT_VERSION, SYSTEM_INSTRUCTION

_ROLES = ("user", "assistant")


class PromptBuildError(ValueError):
    pass


def _context_text(context: Union[str, Mapping]) -> str:
    if isinstance(context, str):
        return context
    if isinstance(context, Mapping):
        if "context" in context and isinstance(context["context"], str):
            return context["context"]
        if "chunks" in context:
            import json
            return json.dumps(context, ensure_ascii=False)
    raise PromptBuildError("legal_context phải là chuỗi hoặc context object hợp lệ.")


def _history(history: Optional[Iterable[Union[HistoryTurn, Mapping]]]) -> tuple[HistoryTurn, ...]:
    turns = []
    for item in history or ():
        if isinstance(item, HistoryTurn):
            turn = item
        elif isinstance(item, Mapping):
            turn = HistoryTurn(str(item.get("role", "")), str(item.get("content", "")))
        else:
            raise PromptBuildError("history item không hợp lệ.")
        if turn.role not in _ROLES or not turn.content.strip():
            raise PromptBuildError("history chỉ nhận role user/assistant và content không rỗng.")
        turns.append(turn)
    return tuple(turns)


class PromptBuilder:
    def __init__(self, params: Optional[LLMParams] = None):
        self.params = params or LLMParams()

    def build(
        self,
        question: str,
        context: Union[str, Mapping],
        history: Optional[Iterable[Union[HistoryTurn, Mapping]]] = None,
        *,
        original_question: Optional[str] = None,
    ) -> LLMInput:
        question = (question or "").strip()
        ctx = _context_text(context).strip()
        if not question:
            raise PromptBuildError("question không được rỗng.")
        if not ctx:
            raise PromptBuildError("legal_context rỗng: không được gọi LLM khi không có nguồn.")
        original = (original_question or question).strip()
        return LLMInput(
            system_instruction=SYSTEM_INSTRUCTION,
            legal_context=ctx,
            user_question=question,
            output_instruction=OUTPUT_INSTRUCTION,
            history=_history(history),
            original_question=original,
            prompt_version=PROMPT_VERSION,
            params=self.params,
        )
