package com.legalai.backend.chat.stream;

import java.util.Set;
import com.legalai.backend.common.exception.ApiException;
import com.legalai.backend.common.web.RequestParser;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import org.springframework.context.annotation.Profile;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.servlet.mvc.method.annotation.SseEmitter;
import tools.jackson.databind.JsonNode;

@RestController
@Profile("rag")
public class StreamController {
    private final StreamService service;
    private final RequestParser parser;
    public StreamController(StreamService service, RequestParser parser) { this.service = service; this.parser = parser; }
    @PostMapping(value = "/api/v1/chat/stream", consumes = "application/json", produces = "text/event-stream")
    public ResponseEntity<SseEmitter> stream(@RequestBody byte[] body, HttpServletRequest request, HttpServletResponse response) {
        if (!request.getParameterMap().isEmpty()) { throw ApiException.invalid(); }
        JsonNode node = parser.object(body, Set.of("question", "clientRequestId", "conversationId"));
        var id = parser.uuid(parser.text(node, "clientRequestId", 36));
        if (id.version() != 4 || id.variant() != 2) { throw ApiException.invalid(); }
        Long conversation = null;
        if (node.has("conversationId") && !node.get("conversationId").isNull()) {
            var value = node.get("conversationId");
            if (!value.isIntegralNumber() || !value.canConvertToLong()) { throw ApiException.invalid(); }
            conversation = value.asLong();
            if (conversation < 1 || conversation > StreamDtos.MAX_ID) { throw ApiException.invalid(); }
        }
        var accepted = service.open(new StreamDtos.Request(parser.text(node, "question", 2000), id, conversation),
                response.getHeader("X-Request-ID"));
        return ResponseEntity.ok().contentType(MediaType.TEXT_EVENT_STREAM).header("Cache-Control", "no-store")
                .header("X-Accel-Buffering", "no").header("X-Conversation-ID", Long.toString(accepted.turn().meta().conversationId()))
                .body(accepted.emitter());
    }
}
