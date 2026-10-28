/** v2.0 wire types. UI models in index.ts are deliberately separate. */
export interface ChatRequestV2 { question: string; clientRequestId: string; conversationId?: number | null }
export interface ChatMeta {
  conversationId: number; clientRequestId: string; userMessageId: number;
  assistantMessageId: number; createdAt: string;
}
export interface PublicCitation {
  citationId: string; chunkId: string; documentId: string; articleId: string;
  documentTitle: string; article: string; clause: string | null; point: string | null; sourceUrl: string;
}
export interface ChatComplete extends ChatMeta {
  status: "answered" | "insufficient_context"; answer: string; citations: PublicCitation[];
}
export interface PublicConversation { id: number; title: string; createdAt: string; updatedAt: string }
export interface PublicMessage {
  id: number; conversationId: number; clientRequestId: string; sequenceNo: number;
  role: "user" | "assistant"; state: "pending" | "completed" | "failed";
  content: string | null; answerStatus: "answered" | "insufficient_context" | null;
  citations: PublicCitation[]; errorCode: string | null; createdAt: string;
}
export interface PublicArticle {
  documentId: string; documentTitle: string; articleId: string;
  article: string; content: string; sourceUrl: string;
}
