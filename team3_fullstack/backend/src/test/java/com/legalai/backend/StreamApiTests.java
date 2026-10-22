package com.legalai.backend;

import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.net.InetSocketAddress;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.nio.charset.StandardCharsets;
import java.time.Duration;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.UUID;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicInteger;
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
import org.springframework.test.context.bean.override.mockito.MockitoSpyBean;
import static org.mockito.Mockito.*;
import static org.mockito.ArgumentMatchers.*;
import tools.jackson.databind.JsonNode;
import tools.jackson.databind.json.JsonMapper;
import static org.junit.jupiter.api.Assertions.*;

@ActiveProfiles({"rag", "rag-test"})
@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT)
class StreamApiTests {
    private static final JsonMapper JSON = JsonMapper.builder().build();
    private static final HttpServer UPSTREAM = server();
    private static final Map<String, AtomicInteger> CALLS = new ConcurrentHashMap<>();
    private static final Map<String, String> TRACES = new ConcurrentHashMap<>();
    private static final Map<String, JsonNode> INPUTS = new ConcurrentHashMap<>();
    private static volatile CountDownLatch gate;
    @Value("${local.server.port}") private int port;
    @MockitoSpyBean private ChatStore store;
    private final HttpClient client = HttpClient.newBuilder().connectTimeout(Duration.ofSeconds(2)).build();
    private record Frame(String event, JsonNode data) { }
    @DynamicPropertySource static void properties(DynamicPropertyRegistry r) {
        r.add("app.rag.base-url", () -> "http://127.0.0.1:" + UPSTREAM.getAddress().getPort());
        r.add("app.rag.timeout-ms", () -> 1500);
    }
    @AfterAll static void stop() { UPSTREAM.stop(0); }
    private static HttpServer server() {
        try {
            var server = HttpServer.create(new InetSocketAddress("127.0.0.1", 0), 0);
            server.createContext("/internal/v1/documents/", e -> {
                String path=e.getRequestURI().getPath();
                TRACES.put("article:"+path,e.getRequestHeaders().getFirst("X-Request-ID"));
                int status=200;
                String result="{\"document_id\":\"mock_v1\",\"document_title\":\"Văn bản kiểm thử\",\"article_id\":\"art1\",\"article\":\"Điều 1\",\"content\":\"Nguyên văn kiểm thử 😀\",\"source_url\":\"https://example.com/mock-law\"}";
                if(path.endsWith("/missing")) {
                    status=404;result="{\"error\":{\"code\":\"ARTICLE_NOT_FOUND\",\"message\":\"Không có Điều\",\"retryable\":false}}";
                }
                byte[] bytes=result.getBytes(StandardCharsets.UTF_8);e.getResponseHeaders().set("Content-Type","application/json");
                try { e.sendResponseHeaders(status,bytes.length);e.getResponseBody().write(bytes); } finally { e.close(); }
            });
            server.createContext("/internal/v1/query", e -> {
                var input = JSON.readTree(e.getRequestBody().readAllBytes());
                String q = input.get("question").asString();
                CALLS.computeIfAbsent(q, k -> new AtomicInteger()).incrementAndGet();
                TRACES.put(q, e.getRequestHeaders().getFirst("X-Request-ID")); INPUTS.put(q, input);
                try {
                    if (q.startsWith("hold")) { gate.await(5, TimeUnit.SECONDS); }
                    if (q.startsWith("timeout")) { Thread.sleep(2000); }
                } catch (InterruptedException interrupted) { Thread.currentThread().interrupt(); }
                int status = 200;
                String result = HttpAiClientTests.answered();
                if (q.startsWith("insufficient")) { result = "{\"status\":\"insufficient_context\",\"answer\":\"Chưa đủ căn cứ.\",\"citations\":[]}"; }
                if (q.startsWith("invalid")) { result = result.replace("[C1]", "[C2]"); }
                if (q.startsWith("unavailable")) { status = 503; result = "{\"error\":{\"code\":\"LLM_UNAVAILABLE\",\"message\":\"private-secret\",\"retryable\":true}}"; }
                byte[] bytes = result.getBytes(StandardCharsets.UTF_8);
                e.getResponseHeaders().set("Content-Type", "application/json");
                try { e.sendResponseHeaders(status, bytes.length); e.getResponseBody().write(bytes); }
                finally { e.close(); }
            });
            server.start(); return server;
        } catch (java.io.IOException e) { throw new IllegalStateException(e); }
    }
    private String body(String q, UUID id, Long conv) {
        var map = new java.util.HashMap<String,Object>(); map.put("question", q); map.put("clientRequestId", id.toString());
        if (conv != null) { map.put("conversationId", conv); }
        return JSON.writeValueAsString(map);
    }
    private HttpRequest post(String path, String body) {
        return HttpRequest.newBuilder(URI.create("http://localhost:" + port + path)).timeout(Duration.ofSeconds(8))
                .header("Content-Type", "application/json").header("Accept", "text/event-stream")
                .POST(HttpRequest.BodyPublishers.ofString(body, StandardCharsets.UTF_8)).build();
    }
    private HttpResponse<String> send(String body) throws Exception {
        return client.send(post("/api/v1/chat/stream", body), HttpResponse.BodyHandlers.ofString(StandardCharsets.UTF_8));
    }
    private List<Frame> frames(String text) {
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
    @Test void sseHasNumericCamelCaseIdsCanonicalCitationAndReplay() throws Exception {
        UUID id = UUID.randomUUID(); String q = "answered-" + id;
        var response = send(body("  " + q + "  ", id, null));
        assertEquals(200, response.statusCode(), response.body());
        assertTrue(response.headers().firstValue("Content-Type").orElseThrow().startsWith("text/event-stream"));
        assertEquals("no-store", response.headers().firstValue("Cache-Control").orElseThrow());
        var events = frames(response.body());
        assertEquals(List.of("meta", "delta", "complete"), events.stream().map(Frame::event).toList());
        var meta = events.getFirst().data(); var complete = events.getLast().data();
        assertEquals(Set.of("conversationId","clientRequestId","userMessageId","assistantMessageId","createdAt"), Set.copyOf(meta.propertyNames()));
        assertEquals(8, complete.size());
        assertTrue(meta.get("conversationId").isIntegralNumber());
        assertEquals(meta.get("conversationId"), complete.get("conversationId"));
        assertEquals(meta.get("createdAt"), complete.get("createdAt"));
        assertEquals(Set.of("citationId","chunkId","documentId","articleId","documentTitle","article","clause","point","sourceUrl"),
                Set.copyOf(complete.get("citations").get(0).propertyNames()));
        assertTrue(complete.get("citations").get(0).get("point").isNull());
        // Export actual wire payloads for the standalone v2.0 schema check in quickstart.
        java.nio.file.Files.writeString(java.nio.file.Path.of("target/vlra41-contract-examples.json"),
                JSON.writeValueAsString(Map.of("ChatRequest",JSON.readTree(body(q,id,null)),
                    "Meta",meta,"Delta",events.get(1).data(),"Complete",complete)),StandardCharsets.UTF_8);
        String trace = response.headers().firstValue("X-Request-ID").orElseThrow(); UUID.fromString(trace);
        assertEquals(trace, TRACES.get(q));
        assertEquals(0, INPUTS.get(q).get("history").size());
        var replay = send(body(q, id, null));
        assertEquals(complete, frames(replay.body()).getLast().data());
        assertNotEquals(trace, replay.headers().firstValue("X-Request-ID").orElseThrow());
        assertEquals(1, CALLS.get(q).get());
        long conv = meta.get("conversationId").asLong();
        var messages = client.send(HttpRequest.newBuilder(URI.create("http://localhost:" + port + "/api/v1/conversations/" + conv + "/messages")).GET().build(), HttpResponse.BodyHandlers.ofString());
        var list = JSON.readTree(messages.body()); assertTrue(list.isArray()); assertEquals(2, list.size()); assertEquals(11, list.get(1).size());
        String next = "follow-" + id;
        assertEquals(200, send(body(next, UUID.randomUUID(), conv)).statusCode());
        assertEquals(2, INPUTS.get(next).get("history").size());
    }
    @Test void insufficientHasNoDeltaOrCitation() throws Exception {
        var response = send(body("insufficient-" + UUID.randomUUID(), UUID.randomUUID(), null));
        var events = frames(response.body());
        assertEquals(List.of("meta", "complete"), events.stream().map(Frame::event).toList());
        assertEquals("insufficient_context", events.getLast().data().get("status").asString());
        assertEquals(0, events.getLast().data().get("citations").size());
    }
    @Test void upstreamErrorsTerminateStreamAndReplayLogicalHttpStatus() throws Exception {
        for (var test : List.of(new String[]{"invalid", "502", "UPSTREAM_INVALID_RESPONSE"},
                new String[]{"unavailable", "503", "SERVICE_UNAVAILABLE"}, new String[]{"timeout", "504", "UPSTREAM_TIMEOUT"})) {
            var id = UUID.randomUUID(); String q = test[0] + id;
            var response = send(body(q,id,null)); var events = frames(response.body());
            assertEquals(200, response.statusCode());
            assertEquals(List.of("meta", "error"), events.stream().map(Frame::event).toList());
            assertEquals(test[2], events.getLast().data().get("error").get("code").asString());
            assertFalse(response.body().contains("private-secret"));
            var replay = send(body(q,id,null));
            assertEquals(Integer.parseInt(test[1]), replay.statusCode(), replay.body());
            assertTrue(replay.headers().firstValue("Content-Type").orElseThrow().startsWith("application/json"));
            assertEquals(1, CALLS.get(q).get());
        }
    }
    @Test void metaIsSentAfterAcceptanceWhilePendingAndBusyIsRejected() throws Exception {
        gate = new CountDownLatch(1); var id = UUID.randomUUID(); String q = "hold-" + id;
        var response = client.send(post("/api/v1/chat/stream",body(q,id,null)),HttpResponse.BodyHandlers.ofInputStream());
        try (var reader = new BufferedReader(new InputStreamReader(response.body(), StandardCharsets.UTF_8))) {
            String first = readFrame(reader); var meta = frames(first).getFirst().data();
            long conv = meta.get("conversationId").asLong();
            assertEquals("pending", store.messages(conv).getLast().state());
            var pending = send(body(q,id,null)); assertEquals(409,pending.statusCode());
            assertTrue(pending.body().contains("REQUEST_IN_PROGRESS"));
            var busy = send(body("new",UUID.randomUUID(),conv)); assertEquals(409,busy.statusCode());
            assertTrue(busy.body().contains("CONVERSATION_BUSY"));
            String heartbeat = readFrame(reader); assertTrue(heartbeat.contains(":heartbeat") || heartbeat.contains(": heartbeat"));
            gate.countDown();
            String rest = reader.lines().collect(java.util.stream.Collectors.joining("\n"));
            assertTrue(rest.contains("event:complete"));
            assertEquals("completed",store.messages(conv).getLast().state());
        } finally { gate.countDown(); }
    }
    @Test void disconnectDoesNotCancelWorkAndReplayDoesNotCallAiAgain() throws Exception {
        gate = new CountDownLatch(1); var id = UUID.randomUUID(); String q = "hold-disconnect-" + id;
        var response = client.send(post("/api/v1/chat/stream",body(q,id,null)),HttpResponse.BodyHandlers.ofInputStream());
        long conv;
        try (var reader = new BufferedReader(new InputStreamReader(response.body(), StandardCharsets.UTF_8))) {
            conv = frames(readFrame(reader)).getFirst().data().get("conversationId").asLong();
        } finally { gate.countDown(); }
        long until = System.nanoTime() + TimeUnit.SECONDS.toNanos(5);
        while (store.messages(conv).getLast().state().equals("pending") && System.nanoTime() < until) { Thread.sleep(20); }
        assertEquals("completed",store.messages(conv).getLast().state());
        assertEquals("complete",frames(send(body(q,id,null)).body()).getLast().event());
        assertEquals(1,CALLS.get(q).get());
    }
    @Test void rejectsInvalidInputBeforeCreatingTurn() throws Exception {
        int before = store.conversations().size();
        String valid = body("Q",UUID.randomUUID(),null);
        for (String invalid : List.of("{}", valid.replace("\"Q\"","\" \""), valid.replace("\"Q\"","123"),
                valid.replace("\"question\":", "\"history\":[],\"question\":"),
                valid.substring(0, valid.length()-1)+",\"conversationId\":\"1\"}",
                valid.substring(0, valid.length()-1)+",\"conversationId\":9007199254740992}",
                valid.substring(0, valid.length()-1)+",\"conversationId\":1.0}",
                valid.substring(0, valid.length()-1)+",\"question\":\"Q\"}", valid+" {}")) {
            var response = send(invalid); assertEquals(400,response.statusCode(),response.body());
            assertTrue(response.body().contains("INVALID_REQUEST"));
        }
        assertEquals(before,store.conversations().size());
    }
    @Test void corsAndBodyLimitsAndLegacyRouteAreCorrectForRagProfile() throws Exception {
        var preflight = client.send(HttpRequest.newBuilder(URI.create("http://localhost:"+port+"/api/v1/chat/stream"))
                .header("Origin","http://localhost:5173").header("Access-Control-Request-Method","POST")
                .header("Access-Control-Request-Headers","content-type,accept").method("OPTIONS",HttpRequest.BodyPublishers.noBody()).build(),HttpResponse.BodyHandlers.ofString());
        assertEquals(200,preflight.statusCode()); assertEquals("http://localhost:5173",preflight.headers().firstValue("Access-Control-Allow-Origin").orElseThrow());
        var denied = client.send(HttpRequest.newBuilder(URI.create("http://localhost:"+port+"/api/v1/chat/stream"))
                .header("Origin","https://denied.example").header("Content-Type","application/json")
                .POST(HttpRequest.BodyPublishers.ofString("{}")).build(),HttpResponse.BodyHandlers.ofString());
        assertEquals(403,denied.statusCode()); assertTrue(denied.headers().firstValue("Access-Control-Allow-Origin").isEmpty());
        assertEquals(413,send(" ".repeat(16*1024+1)).statusCode());
        var media = client.send(HttpRequest.newBuilder(URI.create("http://localhost:"+port+"/api/v1/chat/stream"))
                .header("Content-Type","text/plain").header("Accept","text/event-stream")
                .POST(HttpRequest.BodyPublishers.ofString("{}")).build(),HttpResponse.BodyHandlers.ofString());
        assertEquals(415,media.statusCode()); assertTrue(media.body().contains("UNSUPPORTED_MEDIA_TYPE"));
        var queryParameters = client.send(post("/api/v1/chat/stream?scenario=answered",body("Q",UUID.randomUUID(),null)),HttpResponse.BodyHandlers.ofString());
        assertEquals(400,queryParameters.statusCode());
        var legacy = client.send(post("/api/v1/query", "{}"),HttpResponse.BodyHandlers.ofString()); assertEquals(404,legacy.statusCode());
    }
    @Test void commitFailureCannotEmitCompleteAndStoresSafeLogicalError() throws Exception {
        doThrow(new org.springframework.dao.DataAccessResourceFailureException("private-secret"))
                .when(store).complete(any(),any());
        var id=UUID.randomUUID(); String q="persist-failure-"+id;
        var response=send(body(q,id,null)); var events=frames(response.body());
        assertEquals(List.of("meta","error"),events.stream().map(Frame::event).toList());
        assertEquals("PERSISTENCE_UNAVAILABLE",events.getLast().data().get("error").get("code").asString());
        assertFalse(response.body().contains("private-secret"));
        assertEquals(503,send(body(q,id,null)).statusCode());
        assertEquals("failed",store.messages(events.getFirst().data().get("conversationId").asLong()).getLast().state());
    }
    @Test void unexpectedFailureAfterAcceptanceIsSafe500AndReplayedWithoutAi() throws Exception {
        doThrow(new IllegalStateException("private-secret")).when(store).complete(any(),any());
        var id=UUID.randomUUID(); String q="unexpected-"+id;
        var response=send(body(q,id,null)); var events=frames(response.body());
        assertEquals("INTERNAL_ERROR",events.getLast().data().get("error").get("code").asString());
        assertFalse(response.body().contains("private-secret"));
        assertEquals(500,send(body(q,id,null)).statusCode()); assertEquals(1,CALLS.get(q).get());
    }
    @Test void databaseFailureBeforeAcceptanceIsJson503() throws Exception {
        doThrow(new org.springframework.dao.DataAccessResourceFailureException("private-secret")).when(store).accept(any());
        var response=send(body("Q",UUID.randomUUID(),null));
        assertEquals(503,response.statusCode()); assertTrue(response.body().contains("PERSISTENCE_UNAVAILABLE"));
        assertFalse(response.body().contains("private-secret")); assertFalse(response.body().contains("event:meta"));
    }
    @Test void publicArticleMapsSixFieldsAndForwardsAttemptTrace() throws Exception {
        var response=client.send(HttpRequest.newBuilder(URI.create("http://localhost:"+port+"/api/v1/documents/mock_v1?articleId=art1")).GET().build(),HttpResponse.BodyHandlers.ofString(StandardCharsets.UTF_8));
        assertEquals(200,response.statusCode(),response.body());var article=JSON.readTree(response.body());
        assertEquals(Set.of("documentId","documentTitle","articleId","article","content","sourceUrl"),Set.copyOf(article.propertyNames()));
        assertEquals("mock_v1",article.get("documentId").asString());assertEquals("Nguyên văn kiểm thử 😀",article.get("content").asString());
        assertEquals(response.headers().firstValue("X-Request-ID").orElseThrow(),TRACES.get("article:/internal/v1/documents/mock_v1/articles/art1"));
    }
    @Test void publicArticleRejectsBadLookupAndDoesNotSubstituteSourceVersion() throws Exception {
        String[][] cases={{"/api/v1/documents/mock_v1","400","INVALID_REQUEST"},
                {"/api/v1/documents/mock_v1?articleId=art1&articleId=art2","400","INVALID_REQUEST"},
                {"/api/v1/documents/mock_v1?articleId=missing","404","ARTICLE_NOT_FOUND"},
                {"/api/v1/documents/mock_v2?articleId=art1","502","UPSTREAM_INVALID_RESPONSE"}};
        for(var c:cases) {
            var response=client.send(HttpRequest.newBuilder(URI.create("http://localhost:"+port+c[0])).GET().build(),HttpResponse.BodyHandlers.ofString());
            assertEquals(Integer.parseInt(c[1]),response.statusCode(),response.body());
            assertEquals(c[2],JSON.readTree(response.body()).get("error").get("code").asString());
        }
    }
    private String readFrame(BufferedReader reader) throws Exception {
        StringBuilder b = new StringBuilder(); String line;
        while ((line=reader.readLine()) != null) { b.append(line).append('\n'); if (line.isEmpty()) { break; } }
        return b.toString();
    }
}
