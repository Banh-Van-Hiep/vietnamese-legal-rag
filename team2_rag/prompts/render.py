"""Render LLM input with explicit boundaries between source data and user data."""
from __future__ import annotations

import re
from dataclasses import dataclass

from team2_rag.llm.types import LLMInput

_BOUNDARY_TAG = re.compile(r"</?(LEGAL_CONTEXT|HISTORY|QUESTION|ORIGINAL_QUESTION)\s*>", re.IGNORECASE)


def neutralize_boundary_tags(text: str) -> str:
    return _BOUNDARY_TAG.sub(lambda m: "&lt;" + m.group(0)[1:], text)


@dataclass(frozen=True)
class RenderedPrompt:
    system: str
    user: str


def render_user_message(request: LLMInput) -> str:
    parts = ["<LEGAL_CONTEXT>\n" + neutralize_boundary_tags(request.legal_context) + "\n</LEGAL_CONTEXT>"]
    if request.history:
        lines = "\n".join(f"{t.role}: {neutralize_boundary_tags(t.content)}" for t in request.history)
        parts.append("<HISTORY>\n" + lines + "\n</HISTORY>")
    parts.append("<ORIGINAL_QUESTION>\n" + neutralize_boundary_tags(request.original_question or request.user_question) + "\n</ORIGINAL_QUESTION>")
    parts.append("<QUESTION>\n" + neutralize_boundary_tags(request.user_question) + "\n</QUESTION>")
    parts.append(request.output_instruction)
    return "\n\n".join(parts)


def render_prompt(request: LLMInput) -> RenderedPrompt:
    return RenderedPrompt(system=request.system_instruction, user=render_user_message(request))
