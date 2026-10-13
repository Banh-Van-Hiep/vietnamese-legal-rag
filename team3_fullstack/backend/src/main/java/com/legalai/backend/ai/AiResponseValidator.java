package com.legalai.backend.ai;

import java.net.URI;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Set;
import java.util.regex.Pattern;
import com.legalai.backend.ai.dto.ArticleResponse;
import com.legalai.backend.ai.dto.Citation;
import com.legalai.backend.ai.dto.RagAnswer;
import com.legalai.backend.common.exception.ApiException;

/** Validates the agreed typed boundary without changing DTOs or fixing bad output. */
public final class AiResponseValidator {
    private static final Pattern MARKER = Pattern.compile("\\[C([0-9]+)\\]");
    private AiResponseValidator() { }

    public static RagAnswer query(RagAnswer result) {
        require(result != null);
        require(result.status() != null && Set.of("answered", "insufficient_context").contains(result.status()));
        text(result.answer(), 12000);
        require(result.citations() != null);
        var mentions = new LinkedHashSet<String>();
        var matcher = MARKER.matcher(result.answer());
        while (matcher.find()) { mentions.add("C" + matcher.group(1)); }
        if ("insufficient_context".equals(result.status())) {
            require(result.citations().isEmpty() && mentions.isEmpty());
            return result;
        }
        List<Citation> citations = result.citations();
        require(!citations.isEmpty() && citations.size() <= 10);
        var ids = new HashSet<String>();
        var chunks = new HashSet<String>();
        for (Citation citation : citations) {
            require(citation != null);
            text(citation.citation_id(), 3);
            require(ids.add(citation.citation_id()));
            text(citation.chunk_id(), 200);
            require(chunks.add(citation.chunk_id()));
            id(citation.document_id(), 200);
            id(citation.article_id(), 100);
            text(citation.document_title(), 500);
            text(citation.article(), 100);
            nullableText(citation.clause(), 100);
            nullableText(citation.point(), 100);
            source(citation.source_url());
        }
        var expected = new ArrayList<String>();
        for (int i=1; i<=citations.size(); i++) { expected.add("C" + i); }
        require(ids.equals(new HashSet<>(expected)));
        require(new ArrayList<>(mentions).equals(expected));
        return result;
    }

    public static ArticleResponse article(ArticleResponse result, String documentId, String articleId) {
        require(result != null);
        id(result.document_id(), 200);
        id(result.article_id(), 100);
        require(result.document_id().equals(documentId) && result.article_id().equals(articleId));
        text(result.document_title(), 500);
        text(result.article(), 100);
        text(result.content(), 200000);
        source(result.source_url());
        return result;
    }

    private static void nullableText(String value, int max) { if (value != null) { text(value, max); } }
    private static void text(String value, int max) {
        require(value != null && !value.isBlank() && value.codePointCount(0, value.length()) <= max);
    }
    private static void id(String value, int max) {
        text(value, max);
        require(value.matches("[A-Za-z0-9_-]+"));
    }
    private static void source(String value) {
        text(value, 2048);
        try {
            URI uri = URI.create(value);
            require(uri.isAbsolute() && "https".equalsIgnoreCase(uri.getScheme()) && uri.getHost() != null);
        } catch (IllegalArgumentException error) { throw invalid(); }
    }
    private static void require(boolean condition) { if (!condition) { throw invalid(); } }
    private static ApiException invalid() {
        return new ApiException(502, "UPSTREAM_INVALID_RESPONSE", "Phản hồi từ dịch vụ xử lý không hợp lệ.", false);
    }
}
