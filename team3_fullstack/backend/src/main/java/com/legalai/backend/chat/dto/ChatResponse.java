package com.legalai.backend.chat.dto;

import java.time.Instant;
import java.util.List;
import java.util.UUID;
import com.legalai.backend.ai.dto.Citation;

public record ChatResponse(UUID conversation_id, UUID client_request_id, UUID user_message_id,
        UUID assistant_message_id, String status, String answer, List<Citation> citations, Instant created_at) { }
