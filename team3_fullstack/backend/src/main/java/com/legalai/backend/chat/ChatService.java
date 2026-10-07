package com.legalai.backend.chat;

import com.legalai.backend.ai.AiClient;
import com.legalai.backend.chat.dto.ChatRequest;
import com.legalai.backend.chat.dto.ChatResponse;
import com.legalai.backend.common.exception.ApiException;
import com.legalai.backend.conversation.ConversationService;
import org.springframework.context.annotation.Profile;
import org.springframework.stereotype.Service;

@Service
@Profile("mock")
public class ChatService {
    private final AiClient ai;
    private final ConversationService conversations;

    public ChatService(AiClient ai, ConversationService conversations) {
        this.ai = ai;
        this.conversations = conversations;
    }

    public ChatResponse query(ChatRequest request) {
        var turn = conversations.accept(request);
        if (turn.response() != null) { return turn.response(); }
        try {
            // AI call occurs outside the synchronized store operation; no DB transaction is held.
            var answer = ai.query(request.question());
            return conversations.complete(turn, answer);
        } catch (ApiException error) {
            throw conversations.fail(turn, error);
        } catch (RuntimeException error) {
            throw conversations.fail(turn, new ApiException(500, "INTERNAL_ERROR", "Hệ thống gặp lỗi khi xử lý yêu cầu.", false));
        }
    }
}
