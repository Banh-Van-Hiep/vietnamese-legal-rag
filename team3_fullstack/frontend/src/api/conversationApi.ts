// API lịch sử hội thoại và xem nguyên văn điều luật.
import { request } from "./client";
import type { Conversation, LegalChunk, Message } from "../types";

export const listConversations = () => request<Conversation[]>("/api/v1/conversations");
export const getMessages = (id: number) =>
  request<Message[]>(`/api/v1/conversations/${id}/messages`);
export const deleteConversation = (id: number) =>
  request<void>(`/api/v1/conversations/${id}`, { method: "DELETE" });
export const getDocument = (docId: string) => request<LegalChunk>(`/api/v1/documents/${docId}`);
