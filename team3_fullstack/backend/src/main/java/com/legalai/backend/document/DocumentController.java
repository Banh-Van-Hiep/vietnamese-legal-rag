package com.legalai.backend.document;

import java.util.Map;
import com.legalai.backend.ai.dto.ArticleResponse;
import com.legalai.backend.common.exception.ApiException;
import com.legalai.backend.common.web.RequestParser;
import org.springframework.context.annotation.Profile;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@RestController
@Profile("mock")
public class DocumentController {
    private final DocumentService service;
    private final RequestParser parser;

    public DocumentController(DocumentService service, RequestParser parser) {
        this.service = service;
        this.parser = parser;
    }

    @GetMapping("/api/v1/documents/{documentId}/articles/{articleId}")
    public ArticleResponse article(@PathVariable String documentId, @PathVariable String articleId,
            @RequestParam Map<String, String> parameters) {
        if (!parameters.isEmpty()) { throw ApiException.invalid(); }
        parser.articleId(documentId, 200);
        parser.articleId(articleId, 100);
        return service.article(documentId, articleId);
    }
}
