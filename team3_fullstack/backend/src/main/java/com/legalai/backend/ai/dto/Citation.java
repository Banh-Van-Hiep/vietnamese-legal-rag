package com.legalai.backend.ai.dto;

public record Citation(String citation_id, String chunk_id, String document_id, String article_id,
        String document_title, String article, String clause, String point, String source_url) { }
