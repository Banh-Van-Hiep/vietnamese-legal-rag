package com.legalai.backend.ai.dto;

/** Internal role/content pair; never carries public identifiers or citation metadata. */
public record HistoryMessage(String role, String content) { }
