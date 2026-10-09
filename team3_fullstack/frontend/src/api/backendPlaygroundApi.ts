import { BASE_URL } from "./client";

// Temporary API playground: field names follow the agreed Team 3 query/article DTOs.
export interface PlaygroundCitation {
  citation_id: string;
  chunk_id: string;
  document_id: string;
  article_id: string;
  document_title: string;
  article: string;
  clause: string | null;
  point: string | null;
  source_url: string;
}

export interface PlaygroundAnswer {
  conversation_id: string;
  client_request_id: string;
  user_message_id: string;
  assistant_message_id: string;
  status: "answered" | "insufficient_context";
  answer: string;
  citations: PlaygroundCitation[];
  created_at: string;
}

export interface PlaygroundArticle {
  document_id: string;
  document_title: string;
  article_id: string;
  article: string;
  content: string;
  source_url: string;
}

export class PlaygroundApiError extends Error {
  constructor(message: string, public status: number, public conversationId: string | null) {
    super(message);
  }
}

async function call<T>(path: string, body?: object, signal?: AbortSignal): Promise<T> {
  const response = await fetch(`${BASE_URL}${path}`, {
    method: body ? "POST" : "GET",
    headers: body ? { "Content-Type": "application/json" } : undefined,
    body: body ? JSON.stringify(body) : undefined,
    signal,
  });
  // Fetch's JSON decoder uses UTF-8, including responses without a charset parameter.
  const data = await response.json();
  if (!response.ok) {
    throw new PlaygroundApiError(
      data.error?.message ?? `Yêu cầu thất bại (HTTP ${response.status}).`,
      response.status,
      response.headers.get("X-Conversation-ID"),
    );
  }
  return data as T;
}

export const checkBackendHealth = (signal?: AbortSignal) =>
  call<{ status: string }>("/api/v1/health", undefined, signal);

export const askBackend = (question: string, conversationId: string | null) =>
  call<PlaygroundAnswer>("/api/v1/query", {
    question,
    client_request_id: crypto.randomUUID(),
    ...(conversationId ? { conversation_id: conversationId } : {}),
  });

export const openBackendArticle = (citation: PlaygroundCitation, signal?: AbortSignal) =>
  call<PlaygroundArticle>(
    `/api/v1/documents/${encodeURIComponent(citation.document_id)}/articles/${encodeURIComponent(citation.article_id)}`,
    undefined,
    signal,
  );
