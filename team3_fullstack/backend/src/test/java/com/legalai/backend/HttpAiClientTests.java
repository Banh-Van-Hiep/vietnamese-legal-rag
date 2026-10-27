package com.legalai.backend;

import java.net.InetSocketAddress;
import java.nio.charset.StandardCharsets;
import java.util.List;
import java.util.UUID;
import java.util.concurrent.atomic.AtomicInteger;
import com.sun.net.httpserver.HttpServer;
import com.legalai.backend.ai.HttpAiClient;
import com.legalai.backend.ai.dto.HistoryMessage;
import com.legalai.backend.common.exception.ApiException;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import tools.jackson.databind.json.JsonMapper;
import static org.junit.jupiter.api.Assertions.*;

class HttpAiClientTests {
    private HttpServer server;
    private HttpAiClient ai;
    private volatile String body = answered();
    private volatile int status = 200;
    private volatile long delay;
    private volatile long bodyDelay;
    private String requestBody;
    private String trace;
    private final AtomicInteger calls = new AtomicInteger();
    static String answered() {
        return """
            {"status":"answered","answer":"Dữ liệu kiểm thử [C1].","citations":[{
            "citation_id":"C1","chunk_id":"mock_v1_art1_clause1","document_id":"mock_v1",
            "article_id":"art1","document_title":"Văn bản kiểm thử","article":"Điều 1",
            "clause":"Khoản 1","point":null,"source_url":"https://example.com/mock-law"}]}
            """;
    }
    @BeforeEach void start() throws Exception {
        server = HttpServer.create(new InetSocketAddress("127.0.0.1", 0), 0);
        server.createContext("/internal/v1/query", exchange -> {
            calls.incrementAndGet();
            requestBody = new String(exchange.getRequestBody().readAllBytes(), StandardCharsets.UTF_8);
            trace = exchange.getRequestHeaders().getFirst("X-Request-ID");
            try { Thread.sleep(delay); } catch (InterruptedException e) { Thread.currentThread().interrupt(); }
            byte[] bytes = body.getBytes(StandardCharsets.UTF_8);
            exchange.getResponseHeaders().set("Content-Type", "application/json; charset=utf-8");
            try {
                exchange.sendResponseHeaders(status, bytes.length);
                if (bodyDelay > 0) {
                    exchange.getResponseBody().write(bytes[0]); exchange.getResponseBody().flush();
                    try { Thread.sleep(bodyDelay); } catch (InterruptedException interrupted) { Thread.currentThread().interrupt(); }
                    exchange.getResponseBody().write(bytes, 1, bytes.length-1);
                } else {
                exchange.getResponseBody().write(bytes);
                }
            } finally { exchange.close(); }
        });
        server.start();
        ai = new HttpAiClient("http://127.0.0.1:" + server.getAddress().getPort(), 1000);
    }
    @AfterEach void stop() { server.stop(0); }

    @Test void sendsOnlyQuestionHistoryAndAttemptTrace() {
        String id = UUID.randomUUID().toString();
        var result = ai.query("Câu hỏi tiếp", List.of(new HistoryMessage("user", "Câu cũ"),
                new HistoryMessage("assistant", "Trả lời cũ")), id);
        assertEquals("answered", result.status());
        assertEquals(id, trace);
        var node = JsonMapper.builder().build().readTree(requestBody);
        assertEquals(java.util.Set.of("question", "history"), java.util.Set.copyOf(node.propertyNames()));
        assertEquals(2, node.get("history").size());
        assertEquals(1, calls.get());
    }
    @Test void acceptsInsufficientWithoutCitation() {
        body = "{\"status\":\"insufficient_context\",\"answer\":\"Chưa đủ căn cứ.\",\"citations\":[]}";
        assertTrue(ai.query("Q").citations().isEmpty());
    }
    @Test void rejectsInvalidOutputWithoutRepair() {
        for (String invalid : List.of(answered().replace("\"point\":null,", ""),
                answered().replace("\"point\":null", "\"point\":123"),
                answered().replace("\"status\":\"answered\"", "\"status\":\"answered\",\"extra\":1"),
                answered().replace("\"status\":\"answered\"", "\"status\":\"answered\",\"status\":\"answered\""),
                answered().replace("[C1]", "[C2]"), answered() + " {}", "not-json")) {
            body = invalid;
            var e = assertThrows(ApiException.class, () -> ai.query("Q"));
            assertEquals("UPSTREAM_INVALID_RESPONSE", e.body().error().code());
        }
    }
    @Test void mapsSafeErrorsAndNeverRetries() {
        String[][] cases = {{"502", "INVALID_LLM_OUTPUT", "502", "UPSTREAM_INVALID_RESPONSE"},
            {"502", "CITATION_INVALID", "502", "UPSTREAM_INVALID_RESPONSE"},
            {"503", "RETRIEVAL_UNAVAILABLE", "503", "SERVICE_UNAVAILABLE"},
            {"503", "LLM_UNAVAILABLE", "503", "SERVICE_UNAVAILABLE"},
            {"504", "LLM_TIMEOUT", "504", "UPSTREAM_TIMEOUT"},
            {"504", "RETRIEVAL_TIMEOUT", "504", "UPSTREAM_TIMEOUT"},
            {"400", "INVALID_REQUEST", "502", "UPSTREAM_CONTRACT_ERROR"},
            {"500", "INTERNAL_ERROR", "502", "UPSTREAM_ERROR"}};
        for (var c : cases) {
            status = Integer.parseInt(c[0]);
            body = "{\"error\":{\"code\":\"" + c[1] + "\",\"message\":\"private-secret\",\"retryable\":true}}";
            var e = assertThrows(ApiException.class, () -> ai.query("Q"));
            assertEquals(Integer.parseInt(c[2]), e.status());
            assertEquals(c[3], e.body().error().code());
            assertFalse(e.getMessage().contains("private-secret"));
        }
        assertEquals(cases.length, calls.get());
    }
    @Test void malformedErrorIsInvalidResponse() {
        status = 503; body = "{\"error\":\"private-secret\"}";
        assertEquals("UPSTREAM_INVALID_RESPONSE", assertThrows(ApiException.class,
                () -> ai.query("Q")).body().error().code());
    }
    @Test void responseBodyTimeoutIsBoundedAndDoesNotRetry() {
        ai = new HttpAiClient("http://127.0.0.1:" + server.getAddress().getPort(), 250);
        bodyDelay = 1000;
        assertEquals(504, assertThrows(ApiException.class, () -> ai.query("Q")).status());
        assertEquals(1, calls.get());
    }
    @Test void connectionFailureIsUnavailable() {
        int port = server.getAddress().getPort(); server.stop(0);
        ai = new HttpAiClient("http://127.0.0.1:" + port, 1000);
        assertEquals(503, assertThrows(ApiException.class, () -> ai.query("Q")).status());
    }
}
