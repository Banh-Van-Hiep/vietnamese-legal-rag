// Kiểu dữ liệu khớp với DTO của backend. Cập nhật khi contracts/ được chốt.
export interface Citation {
  chunkId: string;
  documentTitle: string;
  article: string;
  snippet: string;
}

export interface LegalChunk {
  chunkId: string;
  documentTitle: string;
  article: string;
  content: string;
}

export interface ChatRequest {
  question: string;
  conversationId?: number;
}

export interface ChatResponse {
  conversationId: number;
  answer: string;
  citations: Citation[];
}

export interface Conversation {
  id: number;
  title: string;
}

export interface Message {
  id: number;
  role: "user" | "assistant";
  content: string;
  citations?: Citation[];
}
