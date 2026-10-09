package com.legalai.backend.ai;

import java.util.List;
import com.legalai.backend.ai.dto.ArticleResponse;
import com.legalai.backend.ai.dto.Citation;
import com.legalai.backend.ai.dto.RagAnswer;
import com.legalai.backend.common.exception.ApiException;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Profile;
import org.springframework.stereotype.Component;

/** Structure-only fixtures; scenario control is configuration, never public request data. */
@Component
@Profile("mock")
public class MockAiClient implements AiClient {
    private static final List<String> QUERY_MODES = List.of("answered", "insufficient_context",
            "internal_error", "service_unavailable", "upstream_timeout");
    private static final List<String> ARTICLE_MODES = List.of("success", "internal_error",
            "service_unavailable", "upstream_timeout");
    private static final ArticleResponse ARTICLE = new ArticleResponse("mock_v1", "Văn bản kiểm thử", "art1", "Điều 1",
            "Nội dung đầy đủ của điều luật dùng để kiểm thử.\nKhoản 1. Đoạn mẫu chỉ dùng để kiểm thử cấu trúc.",
            "https://example.com/mock-law");
    private static final Citation CITATION = new Citation("C1", "mock_v1_art1_clause1", ARTICLE.document_id(),
            ARTICLE.article_id(), ARTICLE.document_title(), ARTICLE.article(), "Khoản 1", null, ARTICLE.source_url());
    private final String queryScenario;
    private final String articleScenario;

    public MockAiClient(String answerStatus) { this(answerStatus, answerStatus, "success"); }

    @Autowired
    public MockAiClient(@Value("${app.mock.answer-status:answered}") String answerStatus,
            @Value("${app.mock.query-scenario:${app.mock.answer-status:answered}}") String queryScenario,
            @Value("${app.mock.article-scenario:success}") String articleScenario) {
        if (answerStatus == null || !List.of("answered", "insufficient_context").contains(answerStatus)) {
            throw new IllegalArgumentException("MOCK_ANSWER_STATUS must be answered or insufficient_context");
        }
        if (queryScenario == null || !QUERY_MODES.contains(queryScenario)) {
            throw new IllegalArgumentException("MOCK_QUERY_SCENARIO must be one of " + QUERY_MODES);
        }
        if (articleScenario == null || !ARTICLE_MODES.contains(articleScenario)) {
            throw new IllegalArgumentException("MOCK_ARTICLE_SCENARIO must be one of " + ARTICLE_MODES);
        }
        this.queryScenario = queryScenario;
        this.articleScenario = articleScenario;
    }

    @Override
    public RagAnswer query(String question) {
        failScenario(queryScenario);
        if (queryScenario.equals("insufficient_context")) {
            return new RagAnswer(queryScenario, "Tài liệu được truy xuất chưa đủ căn cứ để trả lời.", List.of());
        }
        return new RagAnswer(queryScenario, "Nội dung trả lời kiểm thử dựa trên đoạn mẫu [C1].", List.of(CITATION));
    }

    @Override
    public ArticleResponse article(String documentId, String articleId) {
        if (!ARTICLE.document_id().equals(documentId)) {
            throw new ApiException(404, "DOCUMENT_NOT_FOUND", "Không tìm thấy văn bản được yêu cầu.", false);
        }
        if (!ARTICLE.article_id().equals(articleId)) {
            throw new ApiException(404, "ARTICLE_NOT_FOUND", "Không tìm thấy điều luật được yêu cầu.", false);
        }
        failScenario(articleScenario);
        return ARTICLE;
    }

    private static void failScenario(String scenario) {
        switch (scenario) {
            case "internal_error" -> throw new ApiException(500, "INTERNAL_ERROR", "Hệ thống gặp lỗi khi xử lý yêu cầu.", false);
            case "service_unavailable" -> throw new ApiException(503, "SERVICE_UNAVAILABLE", "Dịch vụ tạm thời không sẵn sàng.", true);
            case "upstream_timeout" -> throw new ApiException(504, "UPSTREAM_TIMEOUT", "Dịch vụ chưa phản hồi trong thời hạn.", true);
            default -> { }
        }
    }
}
