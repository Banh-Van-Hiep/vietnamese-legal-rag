package com.legalai.backend.ai;

import java.util.List;
import com.legalai.backend.ai.dto.ArticleResponse;
import com.legalai.backend.ai.dto.Citation;
import com.legalai.backend.ai.dto.RagAnswer;
import com.legalai.backend.common.exception.ApiException;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Profile;
import org.springframework.stereotype.Component;

/**
 * Cài đặt giả của {@link AiClient}: trả dữ liệu mẫu để phát triển khi Team 2 chưa xong.
 */
@Component
@Profile("mock")
public class MockAiClient implements AiClient {
    private final String answerStatus;

    public MockAiClient(@Value("${app.mock.answer-status:answered}") String answerStatus) {
        if (!List.of("answered", "insufficient_context").contains(answerStatus)) {
            throw new IllegalArgumentException("MOCK_ANSWER_STATUS must be answered or insufficient_context");
        }
        this.answerStatus = answerStatus;
    }

    @Override
    public RagAnswer query(String question) {
        if (answerStatus.equals("insufficient_context")) {
            return new RagAnswer(answerStatus, "Tài liệu được truy xuất chưa đủ căn cứ để trả lời.", List.of());
        }
        Citation citation = new Citation("C1", "mock_v1_art1_clause1", "mock_v1", "art1",
                "Văn bản kiểm thử", "Điều 1", "Khoản 1", null, "https://example.com/mock-law");
        return new RagAnswer(answerStatus, "Nội dung trả lời kiểm thử dựa trên đoạn mẫu [C1].", List.of(citation));
    }

    @Override
    public ArticleResponse article(String documentId, String articleId) {
        if (!documentId.equals("mock_v1")) {
            throw new ApiException(404, "DOCUMENT_NOT_FOUND", "Không tìm thấy văn bản được yêu cầu.", false);
        }
        if (!articleId.equals("art1")) {
            throw new ApiException(404, "ARTICLE_NOT_FOUND", "Không tìm thấy điều luật được yêu cầu.", false);
        }
        return new ArticleResponse("mock_v1", "Văn bản kiểm thử", "art1", "Điều 1",
                "Nội dung đầy đủ của điều luật dùng để kiểm thử.\nKhoản 1. Đoạn mẫu chỉ dùng để kiểm thử cấu trúc.",
                "https://example.com/mock-law");
    }
}
