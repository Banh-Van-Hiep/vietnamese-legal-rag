// API hỏi đáp: POST /api/v1/query, trả lời đồng bộ (không streaming).
import { request } from "./client";
import type { ChatRequest, ChatResponse } from "../types";

export const sendQuery = (body: ChatRequest, signal?: AbortSignal) =>
  request<ChatResponse>("/api/v1/query", { method: "POST", json: body, signal, timeoutMs: 60_000 });
