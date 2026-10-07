package com.legalai.backend.chat.dto;

import java.util.UUID;

/** Validated public input. IDs belong to Team 3 and are not passed to Python. */
public record ChatRequest(UUID conversation_id, UUID client_request_id, String question) { }
