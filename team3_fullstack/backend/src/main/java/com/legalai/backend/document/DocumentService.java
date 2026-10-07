package com.legalai.backend.document;

import com.legalai.backend.ai.AiClient;
import com.legalai.backend.ai.dto.ArticleResponse;
import org.springframework.context.annotation.Profile;
import org.springframework.stereotype.Service;

@Service
@Profile("mock")
public class DocumentService {
    private final AiClient ai;

    public DocumentService(AiClient ai) { this.ai = ai; }

    public ArticleResponse article(String documentId, String articleId) {
        return ai.article(documentId, articleId);
    }
}
