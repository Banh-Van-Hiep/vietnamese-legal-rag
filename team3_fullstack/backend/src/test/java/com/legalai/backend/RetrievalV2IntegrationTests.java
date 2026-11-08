package com.legalai.backend;

import java.io.IOException;
import java.io.InputStream;
import java.net.InetSocketAddress;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.nio.charset.StandardCharsets;
import java.time.Duration;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.UUID;
import com.sun.net.httpserver.HttpExchange;
import com.sun.net.httpserver.HttpServer;
import com.legalai.backend.conversation.persistence.ChatStore;
import org.junit.jupiter.api.AfterAll;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.test.context.ActiveProfiles;
import org.springframework.test.context.DynamicPropertyRegistry;
import org.springframework.test.context.DynamicPropertySource;
import tools.jackson.databind.JsonNode;
import tools.jackson.databind.json.JsonMapper;
import static org.junit.jupiter.api.Assertions.*;

/**
 * VLRA-63 / VLRA-69: Backend ↔ RAG v2 contract through the public API.
 * The stub AI Service returns payloads built from real Retrieval v2 chunks (src/test/resources/retrieval-v2),
 * payloads that break contracts/v0.1/rag_response.schema.json, and the error bodies the AI Service sends
 * (public codes on develop since 26/10/2026, internal codes before).
 */
@ActiveProfiles({"rag", "rag-test"})
@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT)
class RetrievalV2IntegrationTests {
    private static final JsonMapper JSON = JsonMapper.builder().build();
    private static final String ANSWERED = resource("retrieval-v2/rag_response_answered.json");
    private static final String ARTICLE = resource("retrieval-v2/article_dieu-74.json");
    private static final String DOCUMENT = "luat-59-2020-qh14-v1";
    private static final HttpServer UPSTREAM = server();
    @Value("${local.server.port}") private int port;
    @Autowired private ChatStore store;
    private final HttpClient client = HttpClient.newBuilder().connectTimeout(Duration.ofSeconds(2)).build();
    private record Frame(String event, JsonNode data) { }

    @DynamicPropertySource static void properties(DynamicPropertyRegistry r) {
        r.add("app.rag.base-url", () -> "http://127.0.0.1:" + UPSTREAM.getAddress().getPort());
        r.add("app.rag.timeout-ms", () -> 1500);
        r.add("spring.datasource.url", () -> "jdbc:h2:mem:retrievalv2;MODE=PostgreSQL;DB_CLOSE_DELAY=-1");
    }
    @AfterAll static void stop() { UPSTREAM.stop(0); }

    private static String resource(String path) {
        try (InputStream in = RetrievalV2IntegrationTests.class.getClassLoader().getResourceAsStream(path)) {
            if (in == null) { throw new IllegalStateException("Missing test resource " + path); }
            return new String(in.readAllBytes(), StandardCharsets.UTF_8);
        } catch (IOException e) { throw new IllegalStateException(e); }
    }
    private static String error(String code, boolean retryable) {
        return "{\"error\":{\"code\":\"" + code + "\",\"message\":\"private-detail\",\"retryable\":" + retryable + "}}";
    }
    private static void reply(HttpExchange e, int status, String body) throws IOException {
        byte[] bytes = body.getBytes(StandardCharsets.UTF_8);
        e.getResponseHeaders().set("Content-Type", "application/json");
        try { e.sendResponseHeaders(status, bytes.length); e.getResponseBody().write(bytes); } finally { e.close(); }
    }
    private static HttpServer server() {
        try {
            var server = HttpServer.create(new InetSocketAddress("127.0.0.1", 0), 0);
            server.createContext("/internal/v1/query", e -> {
                String q = JSON.readTree(e.getRequestBody().readAllBytes()).get("question").asString();
                if (q.startsWith("v2-insufficient")) {
                    reply(e, 200, "{\"status\":\"insufficient_context\",\"answer\":\"Chưa đủ căn cứ trong dữ liệu.\",\"citations\":[]}");
                } else if (q.startsWith("v2-unavailable")) { reply(e, 503, error("SERVICE_UNAVAILABLE", true));
                } else if (q.startsWith("v2-retrieval-down")) { reply(e, 503, error("RETRIEVAL_UNAVAILABLE", true));
                } else if (q.startsWith("v2-timeout")) { reply(e, 504, error("UPSTREAM_TIMEOUT", true));
                } else if (q.startsWith("v2-invalid")) { reply(e, 502, error("UPSTREAM_INVALID_RESPONSE", false));
                } else if (q.startsWith("v2-llm-timeout")) { reply(e, 504, error("LLM_TIMEOUT", true));
                } else if (q.startsWith("bad-marker")) { reply(e, 200, ANSWERED.replace("[C1]", "[C3]"));
                } else if (q.startsWith("bad-extra-field")) {
                    reply(e, 200, ANSWERED.replaceFirst("\"status\": \"answered\"", "\"status\": \"answered\", \"warning\": \"low_confidence\""));
                } else if (q.startsWith("bad-missing-point")) { reply(e, 200, ANSWERED.replaceFirst("\"point\": null,\\s*", ""));
                } else if (q.startsWith("bad-insufficient-with-citation")) {
                    reply(e, 200, ANSWERED.replaceFirst("\"status\": \"answered\"", "\"status\": \"insufficient_context\""));
                } else if (q.startsWith("bad-status")) {
                    reply(e, 200, ANSWERED.replaceFirst("\"status\": \"answered\"", "\"status\": \"answered_with_warning\""));
                } else { reply(e, 200, ANSWERED); }
            });
            server.createContext("/internal/v1/documents/", e -> {
                String path = e.getRequestURI().getPath();
                if (path.equals("/internal/v1/documents/" + DOCUMENT + "/articles/dieu-74")) { reply(e, 200, ARTICLE); }
                else if (path.startsWith("/internal/v1/documents/" + DOCUMENT + "/")) { reply(e, 404, error("ARTICLE_NOT_FOUND", false)); }
                else { reply(e, 404, error("DOCUMENT_NOT_FOUND", false)); }
            });
            server.start();
            return server;
        } catch (IOException e) { throw new IllegalStateException(e); }
    }

    private HttpResponse<String> ask(String question) throws Exception {
        var body = new HashMap<String, Object>();
        body.put("question", question); body.put("clientRequestId", UUID.randomUUID().toString());
        var request = HttpRequest.newBuilder(URI.create("http://localhost:" + port + "/api/v1/chat/stream"))
                .timeout(Duration.ofSeconds(8)).header("Content-Type", "application/json").header("Accept", "text/event-stream")
                .POST(HttpRequest.BodyPublishers.ofString(JSON.writeValueAsString(body), StandardCharsets.UTF_8)).build();
        return client.send(request, HttpResponse.BodyHandlers.ofString(StandardCharsets.UTF_8));
    }
    private HttpResponse<String> article(String documentId, String articleId) throws Exception {
        var uri = URI.create("http://localhost:" + port + "/api/v1/documents/" + documentId + "?articleId=" + articleId);
        return client.send(HttpRequest.newBuilder(uri).GET().build(), HttpResponse.BodyHandlers.ofString(StandardCharsets.UTF_8));
    }
    private static List<Frame> frames(String text) {
        var result = new ArrayList<Frame>();
        for (String raw : text.replace("\r\n", "\n").split("\n\n")) {
            String event = null, data = null;
            for (String line : raw.split("\n")) {
                if (line.startsWith("event:")) { event = line.substring(6).strip(); }
                if (line.startsWith("data:")) { data = line.substring(5).strip(); }
            }
            if (event != null && data != null) { result.add(new Frame(event, JSON.readTree(data))); }
        }
        return result;
    }
    private static List<String> names(List<Frame> frames) { return frames.stream().map(Frame::event).toList(); }

    @Test void answeredRetrievalV2ResponseKeepsCitationDataAndOpensSource() throws Exception {
        var response = ask("v2-answered-" + UUID.randomUUID());
        assertEquals(200, response.statusCode(), response.body());
        var events = frames(response.body());
        assertEquals(List.of("meta", "delta", "complete"), names(events));
        var expected = JSON.readTree(ANSWERED);
        var complete = events.getLast().data();
        assertEquals("answered", complete.get("status").asString());
        assertEquals(expected.get("answer").asString(), complete.get("answer").asString());
        assertEquals(expected.get("answer").asString(), events.get(1).data().get("text").asString());

        // Every citation field from the AI Service reaches the client unchanged, only renamed to camelCase.
        var citations = complete.get("citations");
        assertEquals(expected.get("citations").size(), citations.size());
        var fields = Map.of("citationId", "citation_id", "chunkId", "chunk_id", "documentId", "document_id",
                "articleId", "article_id", "documentTitle", "document_title", "article", "article",
                "clause", "clause", "point", "point", "sourceUrl", "source_url");
        for (int i = 0; i < citations.size(); i++) {
            assertEquals(fields.size(), citations.get(i).size());
            for (var field : fields.entrySet()) {
                assertEquals(expected.get("citations").get(i).get(field.getValue()), citations.get(i).get(field.getKey()),
                        "citation " + i + " field " + field.getKey());
            }
        }

        long conversation = events.getFirst().data().get("conversationId").asLong();
        var messages = store.messages(conversation);
        assertEquals(2, messages.size());
        assertEquals("completed", messages.getLast().state());

        // The first citation opens the cited article through the public Viewer endpoint.
        var first = citations.get(0);
        var source = article(first.get("documentId").asString(), first.get("articleId").asString());
        assertEquals(200, source.statusCode(), source.body());
        var opened = JSON.readTree(source.body()); var stored = JSON.readTree(ARTICLE);
        assertEquals(stored.get("document_id"), opened.get("documentId"));
        assertEquals(stored.get("article_id"), opened.get("articleId"));
        assertEquals(stored.get("document_title"), opened.get("documentTitle"));
        assertEquals(stored.get("article"), opened.get("article"));
        assertEquals(stored.get("content"), opened.get("content"));
        assertEquals(stored.get("source_url"), opened.get("sourceUrl"));
    }

    @Test void insufficientContextHasNoDeltaOrCitation() throws Exception {
        var events = frames(ask("v2-insufficient-" + UUID.randomUUID()).body());
        assertEquals(List.of("meta", "complete"), names(events));
        assertEquals("insufficient_context", events.getLast().data().get("status").asString());
        assertEquals(0, events.getLast().data().get("citations").size());
    }

    @Test void aiServiceErrorsFollowArchitectureErrorTable() throws Exception {
        String[][] cases = {
            {"v2-unavailable", "SERVICE_UNAVAILABLE", "true"},
            {"v2-retrieval-down", "SERVICE_UNAVAILABLE", "true"},
            {"v2-timeout", "UPSTREAM_TIMEOUT", "true"},
            {"v2-llm-timeout", "UPSTREAM_TIMEOUT", "true"},
            {"v2-invalid", "UPSTREAM_INVALID_RESPONSE", "false"}};
        for (var c : cases) {
            var response = ask(c[0] + "-" + UUID.randomUUID());
            var events = frames(response.body());
            assertEquals(List.of("meta", "error"), names(events), c[0]);
            var error = events.getLast().data().get("error");
            assertEquals(c[1], error.get("code").asString(), c[0]);
            assertEquals(Boolean.parseBoolean(c[2]), error.get("retryable").asBoolean(), c[0]);
            assertFalse(response.body().contains("private-detail"), c[0]);
            long conversation = events.getFirst().data().get("conversationId").asLong();
            assertEquals("failed", store.messages(conversation).getLast().state(), c[0]);
        }
    }

    @Test void payloadOutsideContractIsRejectedAndNeverCompleted() throws Exception {
        // VLRA-69: marker/citation mismatch, an unapproved field, a dropped nullable key, citations with
        // insufficient_context and an unknown status must never reach the user as a successful answer.
        for (String q : List.of("bad-marker", "bad-extra-field", "bad-missing-point", "bad-insufficient-with-citation",
                "bad-status")) {
            var response = ask(q + "-" + UUID.randomUUID());
            var events = frames(response.body());
            assertEquals(List.of("meta", "error"), names(events), q);
            var error = events.getLast().data().get("error");
            assertEquals("UPSTREAM_INVALID_RESPONSE", error.get("code").asString(), q);
            assertFalse(error.get("retryable").asBoolean(), q);
            assertFalse(response.body().contains("event:complete"), q);
            assertFalse(response.body().contains("event:delta"), q);
            long conversation = events.getFirst().data().get("conversationId").asLong();
            assertEquals("failed", store.messages(conversation).getLast().state(), q);
        }
    }

    @Test void missingSourceKeepsSpecificNotFoundCode() throws Exception {
        var article = article(DOCUMENT, "dieu-999");
        assertEquals(404, article.statusCode(), article.body());
        assertEquals("ARTICLE_NOT_FOUND", JSON.readTree(article.body()).get("error").get("code").asString());
        var document = article("luat-0-0000-xx-v1", "dieu-1");
        assertEquals(404, document.statusCode(), document.body());
        assertEquals("DOCUMENT_NOT_FOUND", JSON.readTree(document.body()).get("error").get("code").asString());
    }
}
