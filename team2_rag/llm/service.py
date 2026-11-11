"""LLM service: prompt -> provider -> output validation, không retry output sai."""
from __future__ import annotations

import dataclasses
import logging
import time
from typing import Callable, Iterable, Mapping, Optional, Union

from team2_rag.llm.base import LLMProvider, ProviderReply
from team2_rag.llm.errors import LLMBadOutputError, LLMError
from team2_rag.llm.output_parser import parse_llm_output
from team2_rag.llm.types import HistoryTurn, LLMInput, LLMParams, LLMResult, Usage
from team2_rag.prompts.render import render_prompt

# Có claims thì JSON dài hơn: 1500 token cắt cụt JSON ở top_k=10 (Gemini finish=MAX_TOKENS, 3/30 câu), 4096 đủ chỗ.
CLAIMS_MIN_OUTPUT_TOKENS = 4096

logger = logging.getLogger("team2_rag.llm")
logger.addHandler(logging.NullHandler())


class LLMService:
    def __init__(self, provider: LLMProvider, *, default_params: Optional[LLMParams] = None,
                 max_retries: int = 0, max_total_seconds: float = 30.0,
                 sleep: Callable[[float], None] = time.sleep,
                 clock: Callable[[], float] = time.monotonic,
                 include_claims: bool = False):
        if max_retries != 0:
            raise ValueError("LLMService không retry mặc định; max_retries phải bằng 0.")
        self.include_claims = include_claims  # True: prompt yêu cầu LLM khai `claims` cho module Verification
        self.provider = provider
        self.default_params = default_params or LLMParams()
        self.max_retries = 0
        self._max_total = max_total_seconds
        self._sleep = sleep
        self._clock = clock

    def generate(self, request: LLMInput, *, request_id: Optional[str] = None, timeout_seconds: Optional[float] = None) -> LLMResult:
        started = self._clock()
        prompt = render_prompt(request)
        original_timeout = getattr(self.provider, "timeout_seconds", None)
        if timeout_seconds is not None and hasattr(self.provider, "timeout_seconds"):
            self.provider.timeout_seconds = timeout_seconds
        try:
            reply = self.provider.complete(prompt, request.params)
        finally:
            if timeout_seconds is not None and original_timeout is not None:
                self.provider.timeout_seconds = original_timeout
        try:
            output = parse_llm_output(reply.text, provider=self.provider.name)
        except LLMBadOutputError:
            raise
        latency_ms = int((self._clock() - started) * 1000)
        # Model thật đã trả lời (Gemini có thể rơi về model dự phòng); provider khác không có `actual_model`.
        model = getattr(reply, "actual_model", None) or getattr(self.provider, "actual_model", self.provider.model)
        logger.info("llm_call request_id=%s provider=%s model=%s prompt_version=%s input_tokens=%s output_tokens=%s latency_ms=%s finish_reason=%s",
                    request_id, self.provider.name, model, request.prompt_version,
                    reply.usage.input_tokens, reply.usage.output_tokens, latency_ms, reply.finish_reason)
        return LLMResult(output, reply.text, self.provider.name, model, reply.usage, latency_ms, reply.finish_reason, 0)

    def ask(self, question: str, context: Union[str, Mapping], history: Optional[Iterable[Union[HistoryTurn, Mapping]]] = None,
            *, request_id: Optional[str] = None, original_question: Optional[str] = None, timeout_seconds: Optional[float] = None) -> LLMResult:
        from team2_rag.prompts.builder import PromptBuilder
        params = self.default_params
        if self.include_claims and (params.max_output_tokens or 0) < CLAIMS_MIN_OUTPUT_TOKENS:
            params = dataclasses.replace(params, max_output_tokens=CLAIMS_MIN_OUTPUT_TOKENS)
        request = PromptBuilder(params=params, include_claims=self.include_claims).build(question, context, history, original_question=original_question)
        return self.generate(request, request_id=request_id, timeout_seconds=timeout_seconds)
