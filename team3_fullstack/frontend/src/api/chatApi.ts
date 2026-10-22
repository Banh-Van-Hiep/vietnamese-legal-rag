// UI request model is adapted explicitly to the public v2.0 SSE contract.
import type { ChatRequest, ChatResponse } from "../types";
import { streamChat } from "./chatStream";
import { citationModel, numericId } from "./publicApi";

export async function sendQuery(body: ChatRequest, options: Omit<NonNullable<Parameters<typeof streamChat>[1]>, "timeoutMs"> = {}): Promise<ChatResponse> {
  const result = await streamChat({ question: body.question, clientRequestId: body.client_request_id,
    ...(body.conversation_id == null ? {} : { conversationId: numericId(body.conversation_id) }) }, options);
  return { conversation_id: String(result.conversationId), client_request_id: result.clientRequestId,
    user_message_id: String(result.userMessageId), assistant_message_id: String(result.assistantMessageId),
    status: result.status, answer: result.answer, citations: result.citations.map(citationModel), created_at: result.createdAt };
}
