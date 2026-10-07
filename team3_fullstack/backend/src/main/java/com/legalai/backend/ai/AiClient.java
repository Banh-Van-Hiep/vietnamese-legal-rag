package com.legalai.backend.ai;

import com.legalai.backend.ai.dto.ArticleResponse;
import com.legalai.backend.ai.dto.RagAnswer;

/**
 * Hợp đồng duy nhất để backend gọi dịch vụ AI (Python, Team 2).
 * Các lớp khác chỉ phụ thuộc interface này, không biết là mock hay HTTP.
 */
public interface AiClient {
    // Mock boundary only. Internal multi-turn/history must be agreed before HTTP integration.
    RagAnswer query(String question);
    ArticleResponse article(String documentId, String articleId);
}
