package com.legalai.backend;

import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.nio.charset.StandardCharsets;
import java.util.Set;
import java.util.UUID;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.ValueSource;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.test.context.SpringBootTest;
import tools.jackson.databind.JsonNode;
import tools.jackson.databind.json.JsonMapper;
import static org.junit.jupiter.api.Assertions.*;

@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT,
        properties = "app.mock.answer-status=answered")
class MockApiTests {
    @Value("${local.server.port}") private int port;
    private final HttpClient client = HttpClient.newHttpClient();
    private final JsonMapper mapper = JsonMapper.builder().build();
    private String requestId;

    @BeforeEach void newRequest() { requestId = UUID.randomUUID().toString(); }

    private HttpResponse<String> send(String method, String path, String body, String... headers) throws Exception {
        var builder = HttpRequest.newBuilder(URI.create("http://localhost:" + port + path))
                .method(method, body == null ? HttpRequest.BodyPublishers.noBody()
                        : HttpRequest.BodyPublishers.ofString(body, StandardCharsets.UTF_8));
        if (headers.length > 0) { builder.headers(headers); }
        return client.send(builder.build(), HttpResponse.BodyHandlers.ofString(StandardCharsets.UTF_8));
    }

    private HttpResponse<String> post(String path, String body) throws Exception {
        return send("POST", path, body, "Content-Type", "application/json");
    }

    private String query(String question) {
        return "{\"client_request_id\":\"" + requestId + "\",\"question\":\"" + question + "\"}";
    }

    private JsonNode json(HttpResponse<String> response) { return mapper.readTree(response.body()); }
    private String field(JsonNode node, String name) { return node.get(name).asString(); }

    private void error(HttpResponse<String> response, int status, String code) {
        assertEquals(status, response.statusCode(), response.body());
        JsonNode root = json(response);
        assertEquals(Set.of("error"), Set.copyOf(root.propertyNames()));
        assertEquals(Set.of("code", "message", "retryable"), Set.copyOf(root.get("error").propertyNames()));
        assertEquals(code, field(root.get("error"), "code"));
        assertTrue(root.get("error").get("retryable").isBoolean());
        assertTrue(response.headers().firstValue("X-Request-ID").isPresent());
    }

    @Test void queryReturnsContractAndReplayDoesNotCreateMessages() throws Exception {
        String body = query("  Câu hỏi kiểm thử  ");
        var first = post("/api/v1/query", body);
        assertEquals(200, first.statusCode(), first.body());
        var result = json(first);
        assertEquals(Set.of("conversation_id", "client_request_id", "user_message_id", "assistant_message_id",
                "status", "answer", "citations", "created_at"), Set.copyOf(result.propertyNames()));
        assertEquals(requestId, field(result, "client_request_id"));
        String conversation = field(result, "conversation_id");
        assertEquals(conversation, first.headers().firstValue("X-Conversation-ID").orElseThrow());
        assertEquals(4, UUID.fromString(conversation).version());
        assertEquals("answered", field(result, "status"));
        assertTrue(field(result, "answer").contains("[C1]"));
        assertEquals(1, result.get("citations").size());
        JsonNode citation = result.get("citations").get(0);
        assertEquals(Set.of("citation_id", "chunk_id", "document_id", "article_id", "document_title",
                "article", "clause", "point", "source_url"), Set.copyOf(citation.propertyNames()));
        assertTrue(citation.get("point").isNull());
        assertTrue(field(result, "created_at").endsWith("Z"));
        var replay = post("/api/v1/query", query("Câu hỏi kiểm thử"));
        assertEquals(result, json(replay));
        assertNotEquals(first.headers().firstValue("X-Request-ID"), replay.headers().firstValue("X-Request-ID"));
        var explicitReplay = post("/api/v1/query", query("Câu hỏi kiểm thử").replace("}", ",\"conversation_id\":\"" + conversation + "\"}"));
        assertEquals(result, json(explicitReplay));
        var history = json(send("GET", "/api/v1/conversations/" + conversation + "/messages", null));
        assertEquals(2, history.get("total_elements").asInt());
        assertEquals("Câu hỏi kiểm thử", field(history.get("items").get(0), "content"));
        assertEquals("completed", field(history.get("items").get(1), "state"));
        assertEquals(2, history.get("items").get(1).get("sequence_no").asInt());
        requestId = UUID.randomUUID().toString();
        var followup = post("/api/v1/query", query("Câu tiếp theo").replace("}", ",\"conversation_id\":\"" + conversation + "\"}"));
        assertEquals(conversation, field(json(followup), "conversation_id"));
        var lastPage = json(send("GET", "/api/v1/conversations/" + conversation + "/messages?page=1&size=2", null));
        assertEquals(4, lastPage.get("total_elements").asInt());
        assertEquals(3, lastPage.get("items").get(0).get("sequence_no").asInt());
    }

    @Test void nullConversationCreatesAndDeletedRequestDoesNotRecreate() throws Exception {
        String body = query("Kiểm thử").replace("}", ",\"conversation_id\":null}");
        var result = json(post("/api/v1/query", body));
        String path = "/api/v1/conversations/" + field(result, "conversation_id");
        var deleted = send("DELETE", path, null);
        assertEquals(204, deleted.statusCode());
        assertEquals("", deleted.body());
        error(send("GET", path, null), 404, "CONVERSATION_NOT_FOUND");
        error(post("/api/v1/query", body), 404, "REQUEST_NOT_FOUND");
    }

    @Test void conflictsAndMissingConversation() throws Exception {
        post("/api/v1/query", query("Câu hỏi một"));
        error(post("/api/v1/query", query("Câu hỏi hai")), 409, "REQUEST_ID_CONFLICT");
        error(post("/api/v1/query", query("Câu hỏi một").replace("}", ",\"conversation_id\":\"" + UUID.randomUUID() + "\"}")),
                409, "REQUEST_ID_CONFLICT");
        requestId = UUID.randomUUID().toString();
        error(post("/api/v1/query", query("Kiểm thử").replace("}", ",\"conversation_id\":\"" + UUID.randomUUID() + "\"}")),
                404, "CONVERSATION_NOT_FOUND");
    }

    @ParameterizedTest
    @ValueSource(strings = {"{}", "[]", "null", "{", "{\"question\":\"x\"}",
            "{\"question\":\"x\",\"client_request_id\":\"bad\"}",
            "{\"question\":\"x\",\"client_request_id\":\"11111111-1111-1111-8111-111111111111\"}"})
    void invalidJsonAndMissingRequiredFields(String body) throws Exception {
        error(post("/api/v1/query", body), 400, "INVALID_REQUEST");
    }

    @Test void rejectsCoercionUnknownDuplicateAndInvalidIds() throws Exception {
        String valid = query("Kiểm thử");
        for (String body : new String[] {
                valid.replace("\"Kiểm thử\"", "123"), valid.replace("\"Kiểm thử\"", "null"),
                valid.replace("\"Kiểm thử\"", "true"), valid.replace("\"Kiểm thử\"", "[]"),
                query("   "), query("a".repeat(2001)),
                valid.replace("}", ",\"unknown\":true}"), valid.replace("}", ",\"question\":\"x\"}"),
                valid + " {}", valid.replace("}", ",\"conversation_id\":123}"),
                valid.replace("}", ",\"conversation_id\":\"\"}"),
                valid.replace("}", ",\"conversation_id\":\"1-1-1-1-1\"}")}) {
            error(post("/api/v1/query", body), 400, "INVALID_REQUEST");
        }
    }

    @Test void questionLimitUsesCodePointsInsteadOfUtf16Units() throws Exception {
        assertEquals(200, post("/api/v1/query", query("😀".repeat(2000))).statusCode());
        requestId = UUID.randomUUID().toString();
        error(post("/api/v1/query", query("😀".repeat(2001))), 400, "INVALID_REQUEST");
    }

    @Test void bodyLimitMediaTypeMethodAndUnknownPath() throws Exception {
        var oversized = send("POST", "/api/v1/query", query("a".repeat(17000)),
                "Content-Type", "application/json", "Origin", "http://localhost:5173");
        error(oversized, 413, "PAYLOAD_TOO_LARGE");
        assertEquals("http://localhost:5173", oversized.headers().firstValue("Access-Control-Allow-Origin").orElseThrow());
        error(send("POST", "/api/v1/query", query("Kiểm thử"), "Content-Type", "text/plain"), 415, "UNSUPPORTED_MEDIA_TYPE");
        var wrongMethod = send("GET", "/api/v1/query", null);
        error(wrongMethod, 405, "METHOD_NOT_ALLOWED");
        assertTrue(wrongMethod.headers().firstValue("Allow").orElseThrow().contains("POST"));
        error(send("GET", "/api/v1/unknown", null), 404, "NOT_FOUND");
    }

    @Test void conversationsUsePagedEnvelopeAndValidateTitleAndPagination() throws Exception {
        var created = post("/api/v1/conversations", "{}");
        assertEquals(201, created.statusCode());
        assertEquals("Hội thoại mới", field(json(created), "title"));
        String path = created.headers().firstValue("Location").orElseThrow();
        assertEquals(json(created), json(send("GET", path, null)));
        var empty = json(send("GET", path + "/messages", null));
        assertEquals(0, empty.get("total_pages").asInt());
        assertEquals(0, empty.get("items").size());
        var page = json(send("GET", "/api/v1/conversations?page=2147483647&size=100", null));
        assertEquals(Set.of("items", "page", "size", "total_elements", "total_pages"), Set.copyOf(page.propertyNames()));
        assertEquals(0, page.get("items").size());
        var titled = post("/api/v1/conversations", "{\"title\":\"  Tra cứu  \"}");
        assertEquals("Tra cứu", field(json(titled), "title"));
        for (String body : new String[] {"{\"title\":null}", "{\"title\":\"  \"}", "{\"title\":123}",
                "{\"title\":\"" + "a".repeat(101) + "\"}", "{\"extra\":1}"}) {
            error(post("/api/v1/conversations", body), 400, "INVALID_REQUEST");
        }
        for (String query : new String[] {"page=-1", "size=0", "size=101", "page=1.2", "page=abc",
                "page=999999999999", "page=0&page=1", "other=1"}) {
            error(send("GET", "/api/v1/conversations?" + query, null), 400, "INVALID_REQUEST");
        }
        error(send("GET", "/api/v1/conversations/not-a-uuid/messages", null), 400, "INVALID_REQUEST");
        error(send("GET", "/api/v1/conversations/" + UUID.randomUUID() + "/messages", null), 404, "CONVERSATION_NOT_FOUND");
    }

    @Test void articleAndHealthSchemasAndNoGetBody() throws Exception {
        var article = send("GET", "/api/v1/documents/mock_v1/articles/art1", null);
        assertEquals(200, article.statusCode());
        assertEquals(Set.of("document_id", "document_title", "article_id", "article", "content", "source_url"),
                Set.copyOf(json(article).propertyNames()));
        assertTrue(field(json(article), "content").contains("\n"));
        error(send("GET", "/api/v1/documents/missing/articles/art1", null), 404, "DOCUMENT_NOT_FOUND");
        error(send("GET", "/api/v1/documents/mock_v1/articles/missing", null), 404, "ARTICLE_NOT_FOUND");
        error(send("GET", "/api/v1/documents/mock.v1/articles/art1", null), 400, "INVALID_REQUEST");
        assertEquals("up", field(json(send("GET", "/api/v1/health", null)), "status"));
        error(send("GET", "/api/v1/health?extra=1", null), 400, "INVALID_REQUEST");
        error(send("GET", "/api/v1/health", "{}"), 400, "INVALID_REQUEST");
    }

    @Test void corsPreflightAndResponseExposeTraceHeaders() throws Exception {
        var preflight = send("OPTIONS", "/api/v1/query", null, "Origin", "http://localhost:5173",
                "Access-Control-Request-Method", "POST", "Access-Control-Request-Headers", "content-type");
        assertEquals(200, preflight.statusCode(), preflight.body());
        assertEquals("http://localhost:5173", preflight.headers().firstValue("Access-Control-Allow-Origin").orElseThrow());
        var actual = send("POST", "/api/v1/query", query("Kiểm thử"), "Content-Type", "application/json",
                "Origin", "http://localhost:5173");
        assertEquals(200, actual.statusCode());
        String exposed = actual.headers().firstValue("Access-Control-Expose-Headers").orElseThrow();
        assertTrue(exposed.contains("X-Request-ID"));
        assertTrue(exposed.contains("X-Conversation-ID"));
        assertTrue(exposed.contains("Location"));
        var rejected = send("OPTIONS", "/api/v1/query", null, "Origin", "https://unapproved.example",
                "Access-Control-Request-Method", "POST");
        assertEquals(403, rejected.statusCode());
        assertTrue(rejected.headers().firstValue("Access-Control-Allow-Origin").isEmpty());
    }
}
