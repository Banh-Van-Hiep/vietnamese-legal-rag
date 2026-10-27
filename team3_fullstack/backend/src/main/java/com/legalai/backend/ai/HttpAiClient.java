package com.legalai.backend.ai;

import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.time.Duration;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.UUID;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.TimeoutException;
import java.util.concurrent.ExecutionException;
import com.legalai.backend.ai.dto.*;
import com.legalai.backend.common.exception.ApiException;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Profile;
import org.springframework.stereotype.Component;
import tools.jackson.core.StreamReadFeature;
import tools.jackson.databind.DeserializationFeature;
import tools.jackson.databind.JsonNode;
import tools.jackson.databind.json.JsonMapper;

/** The only HTTP boundary to Python. No provider retry or public IDs in the payload. */
@Component
@Profile("rag")
public class HttpAiClient implements AiClient {
    private static final Set<String> CITATION = Set.of("citation_id", "chunk_id", "document_id",
            "article_id", "document_title", "article", "clause", "point", "source_url");
    private final JsonMapper mapper = JsonMapper.builder().enable(StreamReadFeature.STRICT_DUPLICATE_DETECTION)
            .enable(DeserializationFeature.FAIL_ON_TRAILING_TOKENS).build();
    private final HttpClient client = HttpClient.newBuilder().connectTimeout(Duration.ofSeconds(2))
            .followRedirects(HttpClient.Redirect.NEVER).build();
    private final URI base;
    private final long timeoutMs;

    public HttpAiClient(@Value("${app.rag.base-url}") String url,
            @Value("${app.rag.timeout-ms:50000}") long timeoutMs) {
        base = URI.create(url.endsWith("/") ? url : url + "/");
        if (!Set.of("http", "https").contains(base.getScheme()) || base.getHost() == null
                || base.getUserInfo() != null || base.getQuery() != null || base.getFragment() != null
                || timeoutMs < 1 || timeoutMs > 50000) {
            throw new IllegalArgumentException("RAG_BASE_URL or timeout is invalid");
        }
        this.timeoutMs = timeoutMs;
    }
    @Override public RagAnswer query(String question) {
        return query(question, List.of(), UUID.randomUUID().toString());
    }
    @Override public RagAnswer query(String question, List<HistoryMessage> history, String requestId) {
        byte[] bytes = mapper.writeValueAsBytes(Map.of("question", question, "history", history));
        if (bytes.length > 256 * 1024) { throw new ApiException(502, "UPSTREAM_CONTRACT_ERROR",
                "Yêu cầu nội bộ vượt giới hạn cho phép.", false); }
        var request = HttpRequest.newBuilder(base.resolve("internal/v1/query"))
                .timeout(Duration.ofMillis(timeoutMs)).header("Content-Type", "application/json; charset=utf-8")
                .header("Accept", "application/json").header("X-Request-ID", requestId)
                .POST(HttpRequest.BodyPublishers.ofByteArray(bytes)).build();
        JsonNode node = exchange(request, false);
        exact(node, Set.of("status", "answer", "citations"));
        String status = string(node, "status", false), answer = string(node, "answer", false);
        if (!node.get("citations").isArray()) { throw invalid(); }
        var citations = new ArrayList<Citation>();
        for (JsonNode c : node.get("citations")) {
            exact(c, CITATION);
            citations.add(new Citation(string(c, "citation_id", false), string(c, "chunk_id", false),
                    string(c, "document_id", false), string(c, "article_id", false),
                    string(c, "document_title", false), string(c, "article", false),
                    string(c, "clause", true), string(c, "point", true), string(c, "source_url", false)));
        }
        return AiResponseValidator.query(new RagAnswer(status, answer, List.copyOf(citations)));
    }
    @Override public ArticleResponse article(String documentId, String articleId) {
        return article(documentId, articleId, UUID.randomUUID().toString());
    }
    @Override public ArticleResponse article(String documentId, String articleId, String requestId) {
        if (!documentId.matches("[A-Za-z0-9_-]{1,200}") || !articleId.matches("[A-Za-z0-9_-]{1,100}")) {
            throw ApiException.invalid();
        }
        var request = HttpRequest.newBuilder(base.resolve("internal/v1/documents/" + documentId
                + "/articles/" + articleId)).timeout(Duration.ofMillis(timeoutMs))
                .header("Accept", "application/json").header("X-Request-ID", requestId).GET().build();
        JsonNode n = exchange(request, true);
        exact(n, Set.of("document_id", "document_title", "article_id", "article", "content", "source_url"));
        return AiResponseValidator.article(new ArticleResponse(string(n, "document_id", false),
                string(n, "document_title", false), string(n, "article_id", false),
                string(n, "article", false), string(n, "content", false), string(n, "source_url", false)), documentId, articleId);
    }
    private JsonNode exchange(HttpRequest request, boolean article) {
        var future = client.sendAsync(request, HttpResponse.BodyHandlers.ofByteArray());
        HttpResponse<byte[]> response;
        try {
            response = future.get(timeoutMs, TimeUnit.MILLISECONDS);
        } catch (TimeoutException e) {
            future.cancel(true); throw timeout();
        } catch (InterruptedException e) {
            future.cancel(true); Thread.currentThread().interrupt(); throw timeout();
        } catch (ExecutionException e) {
            if (e.getCause() instanceof java.net.http.HttpTimeoutException) { throw timeout(); }
            throw new ApiException(503, "SERVICE_UNAVAILABLE", "Dịch vụ trả lời tạm thời không sẵn sàng.", true);
        }
        String contentType = response.headers().firstValue("Content-Type").orElse("").split(";", 2)[0].strip();
        if (!"application/json".equalsIgnoreCase(contentType) || response.body().length > (article ? 2_000_000 : 262144)) {
            throw invalid();
        }
        JsonNode node;
        try { node = mapper.readTree(response.body()); } catch (RuntimeException e) { throw invalid(); }
        if (response.statusCode() == 200) { return node; }
        exact(node, Set.of("error"));
        var error = node.get("error");
        exact(error, Set.of("code", "message", "retryable"));
        String code = string(error, "code", false);
        if (string(error, "message", false).isBlank() || !error.get("retryable").isBoolean()) { throw invalid(); }
        int status = response.statusCode();
        if (article && status == 404 && Set.of("DOCUMENT_NOT_FOUND", "ARTICLE_NOT_FOUND").contains(code)) {
            throw new ApiException(404, code, "Không tìm thấy nguồn được yêu cầu.", false);
        }
        if (status >= 400 && status < 500) { throw new ApiException(502, "UPSTREAM_CONTRACT_ERROR",
                "Dịch vụ xử lý từ chối yêu cầu nội bộ.", false); }
        if (status == 502 && Set.of("INVALID_LLM_OUTPUT", "CITATION_INVALID").contains(code)) { throw invalid(); }
        if (status == 503 && Set.of("RETRIEVAL_UNAVAILABLE", "LLM_UNAVAILABLE").contains(code)) {
            throw new ApiException(503, "SERVICE_UNAVAILABLE", "Dịch vụ trả lời tạm thời không sẵn sàng.", true);
        }
        if (status == 504 && Set.of("RETRIEVAL_TIMEOUT", "LLM_TIMEOUT").contains(code)) { throw timeout(); }
        throw new ApiException(502, "UPSTREAM_ERROR", "Dịch vụ xử lý gặp lỗi.", false);
    }
    private static void exact(JsonNode node, Set<String> fields) {
        if (node == null || !node.isObject() || !Set.copyOf(node.propertyNames()).equals(fields)) { throw invalid(); }
    }
    private static String string(JsonNode node, String key, boolean nullable) {
        JsonNode value = node.get(key);
        if (value == null) { throw invalid(); }
        if (nullable && value.isNull()) { return null; }
        if (!value.isString()) { throw invalid(); }
        return value.asString();
    }
    private static ApiException invalid() {
        return new ApiException(502, "UPSTREAM_INVALID_RESPONSE", "Phản hồi từ dịch vụ xử lý không hợp lệ.", false);
    }
    private static ApiException timeout() {
        return new ApiException(504, "UPSTREAM_TIMEOUT", "Dịch vụ trả lời vượt thời gian xử lý.", true);
    }
}
