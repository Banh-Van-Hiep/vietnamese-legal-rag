// API lịch sử hội thoại.
import { request } from "./client";
import type { Conversation, Message, PageResponse } from "../types";

const MAX_PAGE_SIZE = 100;

export const listConversations = (signal?: AbortSignal) =>
  request<PageResponse<Conversation>>(`/api/v1/conversations?page=0&size=${MAX_PAGE_SIZE}`, { signal });

export const createConversation = (title: string, signal?: AbortSignal) =>
  request<Conversation>("/api/v1/conversations", { method: "POST", json: { title }, signal });

export const deleteConversation = (id: string) =>
  request<void>(`/api/v1/conversations/${encodeURIComponent(id)}`, { method: "DELETE" });

/** Lấy toàn bộ tin nhắn của hội thoại, theo thứ tự cũ đến mới. */
export async function getAllMessages(id: string, signal?: AbortSignal): Promise<Message[]> {
  const all: Message[] = [];
  for (let page = 0; ; page++) {
    const result = await request<PageResponse<Message>>(
      `/api/v1/conversations/${encodeURIComponent(id)}/messages?page=${page}&size=${MAX_PAGE_SIZE}`,
      { signal },
    );
    all.push(...result.items);
    if (page + 1 >= result.total_pages) return all;
  }
}
