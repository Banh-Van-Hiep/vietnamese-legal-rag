package com.legalai.backend.conversation;

import java.time.Instant;
import java.util.UUID;

/** Public snapshot used by the in-memory mock. Not a JPA entity. */
public record Conversation(UUID conversation_id, String title, Instant created_at, Instant updated_at) {
    public Conversation updated(Instant now) {
        return new Conversation(conversation_id, title, created_at, now);
    }
}
