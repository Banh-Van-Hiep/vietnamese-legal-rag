package com.legalai.backend.conversation;

import java.time.Instant;
import java.util.List;
import java.util.UUID;
import com.legalai.backend.ai.dto.Citation;

/** Public snapshot used by the in-memory mock. Not a JPA entity. */
public record Message(UUID message_id, UUID conversation_id, UUID client_request_id, int sequence_no,
        String role, String state, String content, String answer_status, List<Citation> citations,
        String error_code, Instant created_at) { }
