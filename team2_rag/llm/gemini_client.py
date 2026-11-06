"""Gemini REST adapter."""
from __future__ import annotations
from typing import Optional
from team2_rag.llm.base import LLMProvider, ProviderReply, raise_for_status
from team2_rag.llm.errors import LLMBadOutputError, LLMContentBlockedError, LLMTimeoutError
from team2_rag.llm.http import Transport, UrllibTransport
from team2_rag.llm.types import LLMParams, Usage
from team2_rag.prompts.render import RenderedPrompt

_BLOCKED = {"SAFETY", "RECITATION", "BLOCKLIST", "PROHIBITED_CONTENT", "SPII", "IMAGE_SAFETY"}

class GeminiProvider(LLMProvider):
    name = "gemini"
    default_base_url = "https://generativelanguage.googleapis.com/v1beta"

    def __init__(self, api_key: str, model: str, timeout_seconds: float = 30.0, *, base_url: Optional[str] = None, transport: Optional[Transport] = None, allow_fallback: bool = True):
        self._api_key, self.model = api_key, model.removeprefix("models/")
        self.timeout_seconds = timeout_seconds
        self.base_url = (base_url or self.default_base_url).rstrip("/")
        self.transport = transport or UrllibTransport()
        self.allow_fallback = allow_fallback
        self.actual_model = self.model

    def build_payload(self, prompt: RenderedPrompt, params: LLMParams) -> dict:
        generation = {"responseMimeType": "application/json"}
        if params.temperature is not None:
            generation["temperature"] = params.temperature
        if params.max_output_tokens is not None:
            generation["maxOutputTokens"] = params.max_output_tokens
        return {
            "systemInstruction": {"parts": [{"text": prompt.system}]},
            "contents": [{"role": "user", "parts": [{"text": prompt.user}]}],
            "generationConfig": generation,
        }

    def complete(self, prompt: RenderedPrompt, params: LLMParams) -> ProviderReply:
        import time
        # Ngân sách tổng = self.timeout_seconds (giới hạn <= 30s)
        overall_deadline = time.monotonic() + self.timeout_seconds
        # Khi benchmark hoặc tắt fallback, chỉ chạy đúng model được cấu hình
        fallback_models = ["gemini-flash-lite-latest"] if (self.allow_fallback and self.model != "gemini-flash-lite-latest") else []
        models_to_try = [self.model] + fallback_models
        resp = None
        successful_model = self.model

        for m in models_to_try:
            time_left = overall_deadline - time.monotonic()
            if time_left < 3.0:
                break

            # Lần gọi được dùng hết thời gian còn lại; 503/429 trả về nhanh nên vẫn còn chỗ cho retry và model dự phòng.
            resp = self.transport.post_json(
                f"{self.base_url}/models/{m}:generateContent",
                {"x-goog-api-key": self._api_key},
                self.build_payload(prompt, params),
                time_left,
            )

            # Nếu gặp 503/429 và còn đủ thời gian (>= 4s), thử lại ngắn 1 lần
            if resp.status in (503, 429) and (overall_deadline - time.monotonic()) >= 4.0:
                time.sleep(1.2)
                retry_timeout = max(1.0, overall_deadline - time.monotonic())
                resp = self.transport.post_json(
                    f"{self.base_url}/models/{m}:generateContent",
                    {"x-goog-api-key": self._api_key},
                    self.build_payload(prompt, params),
                    retry_timeout,
                )

            if resp is not None and 200 <= resp.status < 300:
                successful_model = m
                break

        if resp is None:
            raise LLMTimeoutError("Hết ngân sách thời gian chờ phản hồi từ LLM provider.", provider=self.name)
        raise_for_status(self.name, resp.status, resp.json)
        data = resp.json or {}
        if (data.get("promptFeedback") or {}).get("blockReason"):
            raise LLMContentBlockedError("Provider chặn prompt theo chính sách an toàn.", provider=self.name)
        candidates = data.get("candidates") or []
        if not candidates:
            raise LLMBadOutputError("Provider không trả về candidates.", provider=self.name)
        cand = candidates[0]
        finish = cand.get("finishReason")
        if finish in _BLOCKED:
            raise LLMContentBlockedError("Provider chặn nội dung theo chính sách an toàn.", provider=self.name)
        parts = (cand.get("content") or {}).get("parts") or []
        text = "".join(p.get("text", "") for p in parts if not p.get("thought")).strip()
        if text.startswith("```json"):
            text = text[7:]
        elif text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()
        self.actual_model = successful_model
        u = data.get("usageMetadata") or {}
        return ProviderReply(text, Usage(u.get("promptTokenCount"), u.get("candidatesTokenCount")), finish, actual_model=successful_model)
