package com.legalai.backend.ai;

import com.legalai.backend.ai.dto.ArticleResponse;
import com.legalai.backend.ai.dto.RagAnswer;

/**
 * Hợp đồng duy nhất để backend gọi dịch vụ AI (Python, Team 2).
 * Các lớp khác chỉ phụ thuộc interface này, không biết là mock hay HTTP.
 */
public interface AiClient {
    RagAnswer query(String question);
    /** v2.0 internal boundary. Legacy mock intentionally ignores history and trace. */
    default RagAnswer query(String question, java.util.List<com.legalai.backend.ai.dto.HistoryMessage> history,
            String requestId) {
        return query(question);
    }
    ArticleResponse article(String documentId, String articleId);
    default ArticleResponse article(String documentId, String articleId, String requestId) {
        return article(documentId, articleId);
    }
}
