package com.legalai.backend.conversation;

import java.net.URI;
import java.util.List;
import java.util.Set;
import com.legalai.backend.chat.stream.StreamDtos;
import com.legalai.backend.chat.stream.StreamDtos.Conversation;
import com.legalai.backend.chat.stream.StreamDtos.Message;
import com.legalai.backend.common.exception.ApiException;
import com.legalai.backend.common.web.RequestParser;
import com.legalai.backend.conversation.persistence.ChatStore;
import jakarta.servlet.http.HttpServletRequest;
import org.springframework.context.annotation.Profile;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

/** Minimal v2.0 conversation operations needed to reconcile a disconnected chat turn. */
@RestController
@Profile("rag")
@RequestMapping("/api/v1/conversations")
public class StreamConversationController {
    private final ChatStore store;
    private final RequestParser parser;
    public StreamConversationController(ChatStore store, RequestParser parser) { this.store = store; this.parser = parser; }
    @GetMapping public List<Conversation> list(HttpServletRequest request) { noQuery(request); return store.conversations(); }
    @GetMapping("/{id}") public Conversation get(@PathVariable String id, HttpServletRequest request) {
        noQuery(request); return store.conversation(id(id));
    }
    @GetMapping("/{id}/messages") public List<Message> messages(@PathVariable String id, HttpServletRequest request) {
        noQuery(request); return store.messages(id(id));
    }
    @PostMapping(consumes = "application/json")
    public ResponseEntity<Conversation> create(@RequestBody byte[] body, HttpServletRequest request) {
        noQuery(request);
        var node = parser.object(body, Set.of("title"));
        var conversation = store.create(node.has("title") ? parser.text(node, "title", 100) : "Hội thoại mới");
        return ResponseEntity.created(URI.create("/api/v1/conversations/" + conversation.id())).body(conversation);
    }
    @DeleteMapping("/{id}") public ResponseEntity<Void> delete(@PathVariable String id, HttpServletRequest request) {
        noQuery(request); store.delete(id(id)); return ResponseEntity.noContent().build();
    }
    private static void noQuery(HttpServletRequest request) {
        if (!request.getParameterMap().isEmpty()) { throw ApiException.invalid(); }
    }
    private static long id(String raw) {
        try {
            if (!raw.matches("[1-9][0-9]{0,15}")) { throw ApiException.invalid(); }
            long value = Long.parseLong(raw);
            if (value > StreamDtos.MAX_ID) { throw ApiException.invalid(); }
            return value;
        } catch (NumberFormatException e) { throw ApiException.invalid(); }
    }
}
