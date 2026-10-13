package com.legalai.backend.conversation;

import java.net.URI;
import java.util.Map;
import java.util.Set;
import com.legalai.backend.common.exception.ApiException;
import com.legalai.backend.common.web.PageResponse;
import com.legalai.backend.common.web.PageResponse.PageRequest;
import com.legalai.backend.common.web.RequestParser;
import org.springframework.context.annotation.Profile;
import org.springframework.http.ResponseEntity;
import org.springframework.util.MultiValueMap;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@RestController
@Profile("mock")
@RequestMapping("/api/v1/conversations")
public class ConversationController {
    private final ConversationService service;
    private final RequestParser parser;

    public ConversationController(ConversationService service, RequestParser parser) {
        this.service = service;
        this.parser = parser;
    }

    @PostMapping(consumes = "application/json", produces = "application/json")
    public ResponseEntity<Conversation> create(@RequestBody byte[] body, @RequestParam Map<String, String> parameters) {
        noParameters(parameters);
        var node = parser.object(body, Set.of("title"));
        String title = node.has("title") ? parser.text(node, "title", 100) : "Hội thoại mới";
        Conversation conversation = service.create(title);
        return ResponseEntity.created(URI.create("/api/v1/conversations/" + conversation.conversation_id())).body(conversation);
    }

    @GetMapping
    public PageResponse<Conversation> list(@RequestParam MultiValueMap<String, String> parameters) {
        return service.list(PageRequest.parse(parameters));
    }

    @GetMapping("/{id}")
    public Conversation get(@PathVariable String id, @RequestParam Map<String, String> parameters) {
        noParameters(parameters);
        return service.get(parser.uuid(id));
    }

    @GetMapping("/{id}/messages")
    public PageResponse<Message> messages(@PathVariable String id, @RequestParam MultiValueMap<String, String> parameters) {
        return service.messages(parser.uuid(id), PageRequest.parse(parameters));
    }

    @DeleteMapping("/{id}")
    public ResponseEntity<Void> delete(@PathVariable String id, @RequestParam Map<String, String> parameters) {
        noParameters(parameters);
        service.delete(parser.uuid(id));
        return ResponseEntity.noContent().build();
    }

    private void noParameters(Map<String, String> parameters) {
        if (!parameters.isEmpty()) { throw ApiException.invalid(); }
    }
}
