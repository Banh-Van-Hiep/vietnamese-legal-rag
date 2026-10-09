package com.legalai.backend;

import java.util.ArrayList;
import java.util.List;
import java.util.stream.Stream;
import com.legalai.backend.ai.AiResponseValidator;
import com.legalai.backend.ai.MockAiClient;
import com.legalai.backend.ai.dto.ArticleResponse;
import com.legalai.backend.ai.dto.Citation;
import com.legalai.backend.ai.dto.RagAnswer;
import com.legalai.backend.common.exception.ApiException;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.MethodSource;
import static org.junit.jupiter.api.Assertions.*;

class AiResponseValidatorTests {
    private static Citation citation(String id, String chunk) {
        return new Citation(id, chunk, "mock_v1", "art1", "Văn bản kiểm thử", "Điều 1", null, null, "https://example.com/mock-law");
    }
    private static RagAnswer answered(String text, List<Citation> citations) { return new RagAnswer("answered", text, citations); }
    private static void invalid(Runnable action) {
        var error = assertThrows(ApiException.class, action::run);
        assertEquals(502, error.status());
        assertEquals("UPSTREAM_INVALID_RESPONSE", error.body().error().code());
        assertFalse(error.body().error().retryable());
        assertFalse(error.getMessage().isBlank());
    }
    static Stream<RagAnswer> badQueryResults() {
        var c = citation("C1", "chunk1");
        var nullCitation = new ArrayList<Citation>(); nullCitation.add(null);
        return Stream.of(null, new RagAnswer("unknown", "answer", List.of()),
                answered(null, List.of(c)), answered(" ", List.of(c)),
                answered("a".repeat(12001), List.of(c)), answered("text [C1]", null),
                answered("text [C1]", List.of()), answered("text [C1]", nullCitation),
                answered("text", List.of(c)), answered("text [C2]", List.of(c)),
                answered("text [C0]", List.of(c)), answered("text [C01]", List.of(c)),
                answered("text [C11]", List.of(c)),
                answered("text [C2] [C1]", List.of(c, citation("C2", "chunk2"))),
                answered("text [C1]", List.of(c, citation("C2", "chunk2"))),
                answered("text [C1] [C2]", List.of(c, citation("C2", "chunk1"))),
                answered("text [C1]", List.of(c, c)),
                new RagAnswer("insufficient_context", "text [C1]", List.of()),
                new RagAnswer("insufficient_context", "text", List.of(c)));
    }
    @ParameterizedTest @MethodSource("badQueryResults")
    void rejectsMalformedQueryOutputAs502(RagAnswer result) { invalid(() -> AiResponseValidator.query(result)); }

    static Stream<Citation> badCitations() {
        return Stream.of(
                new Citation(null, "chunk", "mock_v1", "art1", "title", "article", null, null, "https://example.com"),
                new Citation("C1", "", "mock_v1", "art1", "title", "article", null, null, "https://example.com"),
                new Citation("C1", "x".repeat(201), "mock_v1", "art1", "title", "article", null, null, "https://example.com"),
                new Citation("C1", "chunk", "doc.id", "art1", "title", "article", null, null, "https://example.com"),
                new Citation("C1", "chunk", "d".repeat(201), "art1", "title", "article", null, null, "https://example.com"),
                new Citation("C1", "chunk", "doc", "a".repeat(101), "title", "article", null, null, "https://example.com"),
                new Citation("C1", "chunk", "doc", "art", "t".repeat(501), "article", null, null, "https://example.com"),
                new Citation("C1", "chunk", "doc", "art", "title", "a".repeat(101), null, null, "https://example.com"),
                new Citation("C1", "chunk", "doc", "art", "title", "article", "", null, "https://example.com"),
                new Citation("C1", "chunk", "doc", "art", "title", "article", null, "p".repeat(101), "https://example.com"),
                new Citation("C1", "chunk", "doc", "art", "title", "article", null, null, "http://example.com"),
                new Citation("C1", "chunk", "doc", "art", "title", "article", null, null, "/relative"),
                new Citation("C1", "chunk", "doc", "art", "title", "article", null, null, "https:opaque"),
                new Citation("C1", "chunk", "doc", "art", "title", "article", null, null, "https://example.com/" + "s".repeat(2048)));
    }
    @ParameterizedTest @MethodSource("badCitations")
    void rejectsCitationShapeAndBounds(Citation citation) { invalid(() -> AiResponseValidator.query(answered("test [C1]", List.of(citation)))); }

    @Test void acceptsUnicodeBoundariesRepeatedMarkersAndUnorderedCitationArray() {
        var c1 = citation("C1", "chunk1"); var c2 = citation("C2", "chunk2");
        var reversed = answered("text [C1] [C2] [C1]", List.of(c2, c1));
        assertSame(reversed, AiResponseValidator.query(reversed));
        var unicodeAnswer = answered("😀".repeat(11996) + "[C1]", List.of(c1));
        assertSame(unicodeAnswer, AiResponseValidator.query(unicodeAnswer));
        invalid(() -> AiResponseValidator.query(answered("😀".repeat(11997) + "[C1]", List.of(c1))));
        var article = new ArticleResponse("doc", "title", "art", "article", "😀".repeat(200000), "https://example.com");
        assertSame(article, AiResponseValidator.article(article, "doc", "art"));
        invalid(() -> AiResponseValidator.article(new ArticleResponse("doc", "title", "art", "article", "😀".repeat(200001), "https://example.com"), "doc", "art"));
        var nullable = new MockAiClient("answered").query("test");
        assertSame(nullable, AiResponseValidator.query(nullable));
    }

    @Test void acceptsTenCitationsAndRejectsEleven() {
        var citations = new ArrayList<Citation>(); var answer = new StringBuilder();
        for (int i=1; i<=10; i++) { citations.add(citation("C"+i, "chunk"+i)); answer.append("[C").append(i).append("] "); }
        assertNotNull(AiResponseValidator.query(answered(answer.toString(), citations)));
        citations.add(citation("C11", "chunk11")); answer.append("[C11]");
        invalid(() -> AiResponseValidator.query(answered(answer.toString(), citations)));
    }

    static Stream<ArticleResponse> badArticles() {
        return Stream.of(null, new ArticleResponse("other", "title", "art1", "article", "content", "https://example.com"),
                new ArticleResponse("mock_v1", "title", "other", "article", "content", "https://example.com"),
                new ArticleResponse("mock_v1", null, "art1", "article", "content", "https://example.com"),
                new ArticleResponse("mock_v1", "title", "art1", "article", null, "https://example.com"),
                new ArticleResponse("mock_v1", "title", "art1", "article", " ", "https://example.com"),
                new ArticleResponse("mock_v1", "title", "art1", "article", "content", null),
                new ArticleResponse("mock_v1", "title", "art1", "article", "content", "http://example.com"));
    }
    @ParameterizedTest @MethodSource("badArticles")
    void rejectsWrongArticleIdentityOrSchema(ArticleResponse result) { invalid(() -> AiResponseValidator.article(result, "mock_v1", "art1")); }
}
