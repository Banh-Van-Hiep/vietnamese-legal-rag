import { v2Conversations, v2CreateConversation, v2DeleteConversation, v2Messages } from "./publicApi";
export const listConversations = v2Conversations;
export const createConversation = v2CreateConversation;
export const deleteConversation = v2DeleteConversation;
export async function getAllMessages(id: string, signal?: AbortSignal) { return v2Messages(id, signal); }
