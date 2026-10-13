package com.legalai.backend.chat;

import java.util.Set;
import com.legalai.backend.chat.dto.ChatRequest;
import com.legalai.backend.chat.dto.ChatResponse;
import com.legalai.backend.common.exception.ApiException;
import com.legalai.backend.common.web.RequestParser;
import org.springframework.context.annotation.Profile;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;
import java.util.Map;

@RestController
@Profile("mock")
public class ChatController {
    private final ChatService service;
    private final RequestParser parser;

    public ChatController(ChatService service, RequestParser parser) {
        this.service = service;
        this.parser = parser;
    }

    @PostMapping(value = "/api/v1/query", consumes = "application/json", produces = "application/json")
    public ResponseEntity<ChatResponse> query(@RequestBody byte[] body, @RequestParam Map<String, String> parameters) {
        if (!parameters.isEmpty()) { throw ApiException.invalid(); }
        var node = parser.object(body, Set.of("question", "client_request_id", "conversation_id"));
        var input = new ChatRequest(parser.optionalConversation(node), parser.requestId(node), parser.text(node, "question", 2000));
        ChatResponse response = service.query(input);
        return ResponseEntity.ok().header("X-Conversation-ID", response.conversation_id().toString()).body(response);
    }
}
