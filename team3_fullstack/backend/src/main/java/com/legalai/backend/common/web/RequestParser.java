package com.legalai.backend.common.web;

import java.util.Set;
import java.util.UUID;
import java.util.regex.Pattern;
import com.legalai.backend.common.exception.ApiException;
import org.springframework.stereotype.Component;
import tools.jackson.core.StreamReadFeature;
import tools.jackson.databind.DeserializationFeature;
import tools.jackson.databind.JsonNode;
import tools.jackson.databind.json.JsonMapper;

@Component
public class RequestParser {
    private static final Pattern UUID_PATTERN = Pattern.compile("[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}");
    private final JsonMapper mapper = JsonMapper.builder()
            .enable(StreamReadFeature.STRICT_DUPLICATE_DETECTION)
            .enable(DeserializationFeature.FAIL_ON_TRAILING_TOKENS).build();

    public JsonNode object(byte[] body, Set<String> allowed) {
        try {
            JsonNode node = mapper.readTree(body);
            if (node == null || !node.isObject()) { throw ApiException.invalid(); }
            for (String key : node.propertyNames()) {
                if (!allowed.contains(key)) { throw ApiException.invalid(); }
            }
            return node;
        } catch (ApiException error) {
            throw error;
        } catch (RuntimeException error) {
            throw ApiException.invalid();
        }
    }

    public String text(JsonNode node, String key, int max) {
        JsonNode value = node.get(key);
        if (value == null || !value.isString()) { throw ApiException.invalid(); }
        String text = value.asString().strip();
        int length = text.codePointCount(0, text.length());
        if (text.isBlank() || length > max) { throw ApiException.invalid(); }
        return text;
    }

    public UUID uuid(String value) {
        if (value == null || !UUID_PATTERN.matcher(value.strip()).matches()) { throw ApiException.invalid(); }
        return UUID.fromString(value.strip());
    }

    public UUID requestId(JsonNode node) {
        UUID id = uuid(text(node, "client_request_id", 36));
        if (id.version() != 4 || id.variant() != 2) { throw ApiException.invalid(); }
        return id;
    }

    public UUID optionalConversation(JsonNode node) {
        if (!node.has("conversation_id") || node.get("conversation_id").isNull()) { return null; }
        return uuid(text(node, "conversation_id", 36));
    }

    public void articleId(String id, int max) {
        if (id == null || id.length() > max || !id.matches("[A-Za-z0-9_-]+")) { throw ApiException.invalid(); }
    }
}
