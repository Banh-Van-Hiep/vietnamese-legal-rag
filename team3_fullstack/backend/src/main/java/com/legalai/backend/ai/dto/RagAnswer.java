package com.legalai.backend.ai.dto;

import java.util.List;

/** Internal RAG result; the backend adds public message and conversation IDs. */
public record RagAnswer(String status, String answer, List<Citation> citations) { }
