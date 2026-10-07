package com.legalai.backend;

import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.util.UUID;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.test.context.SpringBootTest;
import tools.jackson.databind.json.JsonMapper;
import static org.junit.jupiter.api.Assertions.*;

@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT,
        properties = "app.mock.answer-status=insufficient_context")
class InsufficientContextApiTests {
    @Value("${local.server.port}") private int port;

    @Test void insufficientContextIsSuccessfulAndSavedWithNoCitations() throws Exception {
        var client = HttpClient.newHttpClient();
        var response = client.send(HttpRequest.newBuilder(URI.create("http://localhost:" + port + "/api/v1/query"))
                .header("Content-Type", "application/json")
                .POST(HttpRequest.BodyPublishers.ofString("{\"client_request_id\":\"" + UUID.randomUUID()
                        + "\",\"question\":\"Kiểm thử\"}")).build(), HttpResponse.BodyHandlers.ofString());
        assertEquals(200, response.statusCode());
        var mapper = JsonMapper.builder().build();
        var result = mapper.readTree(response.body());
        assertEquals("insufficient_context", result.get("status").asString());
        assertEquals(0, result.get("citations").size());
        assertFalse(result.get("answer").asString().contains("[C"));
        var history = client.send(HttpRequest.newBuilder(URI.create("http://localhost:" + port
                        + "/api/v1/conversations/" + result.get("conversation_id").asString() + "/messages")).GET().build(),
                HttpResponse.BodyHandlers.ofString());
        var assistant = mapper.readTree(history.body()).get("items").get(1);
        assertEquals("completed", assistant.get("state").asString());
        assertEquals("insufficient_context", assistant.get("answer_status").asString());
        assertEquals(0, assistant.get("citations").size());
    }
}
