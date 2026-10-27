// Presentation models. Public v2.0 wire types live in publicApi.ts; adapters map numeric
// IDs to route strings and camelCase to these existing component fields.

export type AnswerStatus = "answered" | "insufficient_context";

export interface Citation {
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

export interface ArticleResponse {
  document_id: string;
  document_title: string;
  article_id: string;
  article: string;
  content: string;
  source_url: string;
}

export interface ChatRequest {
  conversation_id?: string | null;
  client_request_id: string;
  question: string;
}

export interface ChatResponse {
  conversation_id: string;
  client_request_id: string;
  user_message_id: string;
  assistant_message_id: string;
  status: AnswerStatus;
  answer: string;
  citations: Citation[];
  created_at: string;
}

export interface Conversation {
  conversation_id: string;
  title: string;
  created_at: string;
  updated_at: string;
}

export interface Message {
  message_id: string;
  conversation_id: string;
  client_request_id: string;
  sequence_no: number;
  role: "user" | "assistant";
  state: "pending" | "completed" | "failed";
  content: string | null;
  answer_status: AnswerStatus | null;
  citations: Citation[];
  error_code: string | null;
  created_at: string;
}

export interface PageResponse<T> {
  items: T[];
  page: number;
  size: number;
  total_elements: number;
  total_pages: number;
}

/** Tin nhắn như giao diện hiển thị: gộp tin đã lưu trên server và tin đang gửi. */
export interface UiMessage {
  key: string;
  role: "user" | "assistant";
  state: "pending" | "completed" | "failed";
  content: string | null;
  answerStatus: AnswerStatus | null;
  citations: Citation[];
  clientRequestId?: string;
  /** Chỉ có ở tin assistant failed. */
  failure?: {
    message: string;
    code: string;
    requestId: string | null;
    /** Có thể bấm "Thử lại" (lỗi tạm thời hoặc chưa rõ kết quả). */
    retryable: boolean;
    outcomeUnknown?: boolean;
  };
}
