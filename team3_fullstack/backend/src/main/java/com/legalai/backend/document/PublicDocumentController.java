package com.legalai.backend.document;

import com.legalai.backend.common.exception.ApiException;
import com.legalai.backend.common.web.RequestParser;
import jakarta.servlet.http.HttpServletResponse;
import org.springframework.context.annotation.Profile;
import org.springframework.util.MultiValueMap;
import org.springframework.web.bind.annotation.*;

/** v2.0 lookup adapter only; original text still belongs to the internal article store. */
@RestController
@Profile("rag")
public class PublicDocumentController {
    public record PublicArticle(String documentId, String documentTitle, String articleId,
            String article, String content, String sourceUrl) { }
    private final DocumentService documents;
    private final RequestParser parser;
    public PublicDocumentController(DocumentService documents, RequestParser parser) { this.documents = documents; this.parser = parser; }
    @GetMapping(value = "/api/v1/documents/{documentId}", produces = "application/json")
    public PublicArticle article(@PathVariable String documentId, @RequestParam MultiValueMap<String, String> params,
            HttpServletResponse response) {
        if (params.size() != 1 || params.get("articleId") == null || params.get("articleId").size() != 1) { throw ApiException.invalid(); }
        String articleId = params.getFirst("articleId");
        parser.articleId(documentId, 200); parser.articleId(articleId, 100);
        var a = documents.article(documentId, articleId, response.getHeader("X-Request-ID"));
        return new PublicArticle(a.document_id(), a.document_title(), a.article_id(), a.article(), a.content(), a.source_url());
    }
}
