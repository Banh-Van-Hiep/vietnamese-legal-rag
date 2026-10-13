package com.legalai.backend;

import com.legalai.backend.ai.MockAiClient;
import com.legalai.backend.common.exception.ApiException;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

class MockScenarioTests {
    @Test void legacyConstructorsAndExplicitSelectorsRemainCompatible() {
        assertEquals("answered", new MockAiClient("answered").query("test").status());
        assertEquals("insufficient_context", new MockAiClient("insufficient_context").query("test").status());
        assertEquals("answered", new MockAiClient("insufficient_context", "answered", "success").query("test").status());
        assertEquals("insufficient_context", new MockAiClient("answered", "insufficient_context", "success").query("test").status());
    }

    @Test void successFixtureLinksEveryCitationToItsArticle() {
        var ai = new MockAiClient("answered");
        var result = ai.query("test");
        assertEquals(1, result.citations().size());
        for (var citation : result.citations()) {
            var article = ai.article(citation.document_id(), citation.article_id());
            assertEquals(citation.document_id(), article.document_id());
            assertEquals(citation.article_id(), article.article_id());
            assertEquals(citation.document_title(), article.document_title());
            assertEquals(citation.article(), article.article());
            assertEquals(citation.source_url(), article.source_url());
            assertTrue(article.content().contains("\n"));
            assertTrue(article.document_title().contains("kiểm thử"));
        }
        var insufficient = new MockAiClient("insufficient_context").query("test");
        assertTrue(insufficient.citations().isEmpty());
        assertFalse(insufficient.answer().contains("[C"));
    }

    @Test void queryAndArticleErrorModesAreIndependentAndPreserveNotFound() {
        String[] modes = {"internal_error", "service_unavailable", "upstream_timeout"};
        for (int i = 0; i < modes.length; i++) {
            int status = new int[] {500, 503, 504}[i];
            String code = new String[] {"INTERNAL_ERROR", "SERVICE_UNAVAILABLE", "UPSTREAM_TIMEOUT"}[i];
            var query = new MockAiClient("answered", modes[i], "success");
            var error = assertThrows(ApiException.class, () -> query.query("test"));
            assertEquals(status, error.status());
            assertEquals(code, error.body().error().code());
            assertEquals(status != 500, error.body().error().retryable());
            assertNotNull(query.article("mock_v1", "art1"));
            var document = new MockAiClient("answered", "answered", modes[i]);
            assertEquals("answered", document.query("test").status());
            var articleError = assertThrows(ApiException.class, () -> document.article("mock_v1", "art1"));
            assertEquals(status, articleError.status());
            assertEquals(code, articleError.body().error().code());
            assertEquals(status != 500, articleError.body().error().retryable());
            assertEquals("DOCUMENT_NOT_FOUND", assertThrows(ApiException.class, () -> document.article("missing", "art1")).body().error().code());
            assertEquals("ARTICLE_NOT_FOUND", assertThrows(ApiException.class, () -> document.article("mock_v1", "missing")).body().error().code());
        }
    }

    @Test void unsupportedAndBlankConfigurationFailsInsteadOfFallingBack() {
        for (String invalid : new String[] {"", " ", "invalid"}) {
            assertThrows(IllegalArgumentException.class, () -> new MockAiClient("answered", invalid, "success"));
            assertThrows(IllegalArgumentException.class, () -> new MockAiClient("answered", "answered", invalid));
            assertThrows(IllegalArgumentException.class, () -> new MockAiClient(invalid, "answered", "success"));
        }
    }
}
