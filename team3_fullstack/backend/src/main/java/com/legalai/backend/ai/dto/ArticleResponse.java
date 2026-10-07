package com.legalai.backend.ai.dto;

/** Full source article, not a retrieval chunk or generated text. */
public record ArticleResponse(String document_id, String document_title, String article_id,
        String article, String content, String source_url) { }
