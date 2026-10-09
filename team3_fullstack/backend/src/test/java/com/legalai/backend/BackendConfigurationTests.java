package com.legalai.backend;

import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.util.Set;
import java.util.Arrays;
import java.util.Map;
import java.util.UUID;
import javax.sql.DataSource;
import com.legalai.backend.ai.AiClient;
import com.legalai.backend.ai.MockAiClient;
import com.legalai.backend.ai.dto.RagAnswer;
import com.legalai.backend.ai.dto.ArticleResponse;
import com.legalai.backend.common.config.CorsConfig;
import com.legalai.backend.common.exception.ApiException;
import com.legalai.backend.common.web.PageResponse.PageRequest;
import com.legalai.backend.conversation.ConversationService;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.context.TestConfiguration;
import org.springframework.context.ApplicationContext;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Import;
import org.springframework.test.context.ActiveProfiles;
import org.springframework.test.context.bean.override.mockito.MockitoSpyBean;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RestController;
import tools.jackson.databind.json.JsonMapper;
import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.Mockito.doThrow;
import static org.mockito.Mockito.doReturn;

@ActiveProfiles("mock")
@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT,
        properties = "app.cors.allowed-origins=http://127.0.0.1:55173")
@Import(BackendConfigurationTests.ProbeConfiguration.class)
class BackendConfigurationTests {
    @Value("${local.server.port}") private int port;
    @Autowired private ApplicationContext context;
    @Autowired private ConversationService conversations;
    @MockitoSpyBean private MockAiClient mockAi;
    private final HttpClient client = HttpClient.newHttpClient();
    private final JsonMapper mapper = JsonMapper.builder().build();

    @Test void mockStartsWithoutDatabaseAndRegistersOnlyMockAiClient() {
        assertTrue(context.getBeansOfType(DataSource.class).isEmpty());
        assertEquals(1, context.getBeansOfType(AiClient.class).size());
        assertInstanceOf(MockAiClient.class, context.getBean(AiClient.class));
    }

    @Test void corsUsesConfiguredOriginForPreflightAndErrors() throws Exception {
        var preflight = client.send(HttpRequest.newBuilder(uri("/api/v1/query"))
                .header("Origin", "http://127.0.0.1:55173")
                .header("Access-Control-Request-Method", "POST")
                .header("Access-Control-Request-Headers", "content-type")
                .method("OPTIONS", HttpRequest.BodyPublishers.noBody()).build(), HttpResponse.BodyHandlers.ofString());
        assertEquals(200, preflight.statusCode());
        assertEquals("http://127.0.0.1:55173", preflight.headers().firstValue("Access-Control-Allow-Origin").orElseThrow());
        assertTrue(Arrays.stream(preflight.headers().firstValue("Access-Control-Allow-Methods").orElseThrow().split(","))
                .map(String::trim).anyMatch("POST"::equalsIgnoreCase));
        assertTrue(Arrays.stream(preflight.headers().firstValue("Access-Control-Allow-Headers").orElseThrow().split(","))
                .map(String::trim).anyMatch("Content-Type"::equalsIgnoreCase));
        var rejected = client.send(HttpRequest.newBuilder(uri("/api/v1/health"))
                .header("Origin", "http://localhost:5173").GET().build(), HttpResponse.BodyHandlers.ofString());
        assertEquals(403, rejected.statusCode());
        assertTrue(rejected.headers().firstValue("Access-Control-Allow-Origin").isEmpty());
        var failure = get("/api/v1/t01-error-probe/timeout");
        assertEquals("http://127.0.0.1:55173", failure.headers().firstValue("Access-Control-Allow-Origin").orElseThrow());
        String exposed = failure.headers().firstValue("Access-Control-Expose-Headers").orElseThrow();
        assertTrue(exposed.contains("X-Request-ID"));
        assertTrue(exposed.contains("X-Conversation-ID"));
        assertTrue(exposed.contains("Location"));
        assertEquals(ProbeController.CONVERSATION.toString(), failure.headers().firstValue("X-Conversation-ID").orElseThrow());
    }

    @Test void systemErrorsUseSafeEnvelopeAndNeverBusinessStatus() throws Exception {
        for (String type : new String[] {"unexpected", "unavailable", "timeout"}) {
            var response = get("/api/v1/t01-error-probe/" + type);
            int expectedStatus = switch (type) { case "unavailable" -> 503; case "timeout" -> 504; default -> 500; };
            String expectedCode = switch (type) {
                case "unavailable" -> "SERVICE_UNAVAILABLE";
                case "timeout" -> "UPSTREAM_TIMEOUT";
                default -> "INTERNAL_ERROR";
            };
            assertEquals(expectedStatus, response.statusCode());
            assertTrue(response.headers().firstValue("Content-Type").orElseThrow().startsWith("application/json"));
            UUID.fromString(response.headers().firstValue("X-Request-ID").orElseThrow());
            var root = mapper.readTree(response.body());
            assertEquals(Set.of("error"), Set.copyOf(root.propertyNames()));
            var error = root.get("error");
            assertEquals(Set.of("code", "message", "retryable"), Set.copyOf(error.propertyNames()));
            assertEquals(expectedCode, error.get("code").asString());
            assertTrue(error.get("message").isString());
            assertFalse(error.get("message").asString().isBlank());
            assertEquals(!type.equals("unexpected"), error.get("retryable").asBoolean());
            assertFalse(response.body().contains("private-provider-detail"));
            assertFalse(response.body().contains("stackTrace"));
            assertFalse(root.has("answer"));
            assertFalse(root.has("status"));
        }
    }

    @Test void unexpectedQueryFailureAfterAcceptanceKeepsConversationAndSafeError() throws Exception {
        String question = "T01 controlled unexpected failure";
        UUID conversation = conversations.create("T01 error test").conversation_id();
        UUID request = UUID.randomUUID();
        doThrow(new IllegalStateException("private-provider-detail test-secret-sentinel"))
                .when(mockAi).query(question);
        String body = mapper.writeValueAsString(Map.of("conversation_id", conversation.toString(),
                "client_request_id", request.toString(), "question", question));
        var response = client.send(HttpRequest.newBuilder(uri("/api/v1/query"))
                .header("Origin", "http://127.0.0.1:55173")
                .header("Content-Type", "application/json")
                .POST(HttpRequest.BodyPublishers.ofString(body)).build(), HttpResponse.BodyHandlers.ofString());
        assertEquals(500, response.statusCode());
        assertEquals(conversation.toString(), response.headers().firstValue("X-Conversation-ID").orElseThrow());
        UUID.fromString(response.headers().firstValue("X-Request-ID").orElseThrow());
        assertTrue(response.headers().firstValue("Content-Type").orElseThrow().startsWith("application/json"));
        assertEquals("http://127.0.0.1:55173", response.headers().firstValue("Access-Control-Allow-Origin").orElseThrow());
        assertTrue(response.headers().firstValue("Access-Control-Expose-Headers").orElseThrow().contains("X-Conversation-ID"));
        var root = mapper.readTree(response.body());
        assertEquals(Set.of("error"), Set.copyOf(root.propertyNames()));
        assertEquals(Set.of("code", "message", "retryable"), Set.copyOf(root.get("error").propertyNames()));
        assertEquals("INTERNAL_ERROR", root.get("error").get("code").asString());
        assertFalse(root.get("error").get("retryable").asBoolean());
        assertFalse(root.get("error").get("message").asString().isBlank());
        assertFalse(response.body().contains("private-provider-detail"));
        assertFalse(response.body().contains("test-secret-sentinel"));
        assertFalse(response.body().contains("stackTrace"));
        var messages = conversations.messages(conversation, new PageRequest(0, 20)).items();
        assertEquals(request, messages.get(0).client_request_id());
        assertEquals("completed", messages.get(0).state());
        assertEquals("failed", messages.get(1).state());
        assertNull(messages.get(1).answer_status());
        assertNull(messages.get(1).content());
    }

    @Test void invalidQueryResponseFailsAcceptedTurnWithoutLeakingPayload() throws Exception {
        RagAnswer[] invalid = {null, new RagAnswer("unknown", "private-provider-detail", java.util.List.of()),
                new RagAnswer(null, "test-secret-sentinel", java.util.List.of())};
        for (int i = 0; i < invalid.length; i++) {
            String question = "T02 invalid query " + i;
            UUID conversation = conversations.create("T02 response guard").conversation_id();
            UUID request = UUID.randomUUID();
            doReturn(invalid[i]).when(mockAi).query(question);
            String body = mapper.writeValueAsString(Map.of("conversation_id", conversation.toString(),
                    "client_request_id", request.toString(), "question", question));
            var response = client.send(HttpRequest.newBuilder(uri("/api/v1/query"))
                    .header("Content-Type", "application/json").POST(HttpRequest.BodyPublishers.ofString(body)).build(),
                    HttpResponse.BodyHandlers.ofString());
            invalidResponse(response);
            assertEquals(conversation.toString(), response.headers().firstValue("X-Conversation-ID").orElseThrow());
            var messages = conversations.messages(conversation, new PageRequest(0, 20)).items();
            assertEquals(request, messages.get(0).client_request_id());
            assertEquals("failed", messages.get(1).state());
            assertNull(messages.get(1).content());
            assertNull(messages.get(1).answer_status());
        }
    }

    @Test void invalidArticleResponseUsesSafe502WithoutCorrectingTuple() throws Exception {
        ArticleResponse valid = new MockAiClient("answered").article("mock_v1", "art1");
        ArticleResponse[] invalid = {null, new ArticleResponse("wrong", valid.document_title(), "art1",
                valid.article(), "private-provider-detail", valid.source_url()),
                new ArticleResponse("mock_v1", valid.document_title(), "wrong", valid.article(),
                        "test-secret-sentinel", valid.source_url())};
        for (ArticleResponse result : invalid) {
            doReturn(result).when(mockAi).article("mock_v1", "art1");
            invalidResponse(get("/api/v1/documents/mock_v1/articles/art1"));
        }
    }

    private void invalidResponse(HttpResponse<String> response) {
        assertEquals(502, response.statusCode(), response.body());
        UUID.fromString(response.headers().firstValue("X-Request-ID").orElseThrow());
        var root = mapper.readTree(response.body());
        assertEquals(Set.of("error"), Set.copyOf(root.propertyNames()));
        var error = root.get("error");
        assertEquals(Set.of("code", "message", "retryable"), Set.copyOf(error.propertyNames()));
        assertEquals("UPSTREAM_INVALID_RESPONSE", error.get("code").asString());
        assertFalse(error.get("retryable").asBoolean());
        assertFalse(error.get("message").asString().isBlank());
        assertFalse(response.body().contains("private-provider-detail"));
        assertFalse(response.body().contains("test-secret-sentinel"));
        assertFalse(response.body().contains("stackTrace"));
    }

    @Test void invalidCorsConfigurationFailsInsteadOfAllowingAllOrigins() {
        for (String origins : new String[] {"", "*", "http://*.example.com", "localhost:5173",
                "http://localhost:5173/path", "http://localhost:5173,", "http://user@localhost:5173",
                "http://localhost:0", "https://example.com?query=1"}) {
            assertThrows(IllegalArgumentException.class, () -> new CorsConfig(origins), origins);
        }
        assertDoesNotThrow(() -> new CorsConfig("http://localhost:5173, https://example.com"));
    }

    private URI uri(String path) { return URI.create("http://localhost:" + port + path); }

    private HttpResponse<String> get(String path) throws Exception {
        return client.send(HttpRequest.newBuilder(uri(path)).header("Origin", "http://127.0.0.1:55173")
                .GET().build(), HttpResponse.BodyHandlers.ofString());
    }

    @TestConfiguration(proxyBeanMethods = false)
    static class ProbeConfiguration {
        @Bean ProbeController probeController() { return new ProbeController(); }
    }

    /** Test-only controller exercises the shared error handler; no production scenario or endpoint is added. */
    @RestController
    static class ProbeController {
        static final UUID CONVERSATION = UUID.randomUUID();

        @GetMapping("/api/v1/t01-error-probe/{type}")
        public void fail(@PathVariable String type) {
            switch (type) {
                case "unavailable" -> throw new ApiException(503, "SERVICE_UNAVAILABLE", "Dịch vụ tạm thời không sẵn sàng.", true, CONVERSATION);
                case "timeout" -> throw new ApiException(504, "UPSTREAM_TIMEOUT", "Dịch vụ chưa phản hồi trong thời hạn.", true, CONVERSATION);
                default -> throw new IllegalStateException("private-provider-detail");
            }
        }
    }
}
