package com.legalai.backend.conversation.persistence;

import java.sql.Timestamp;
import java.time.Instant;
import java.util.UUID;
import com.legalai.backend.ai.MockAiClient;
import com.legalai.backend.chat.stream.StreamDtos.Request;
import com.legalai.backend.common.exception.ApiException;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.test.annotation.DirtiesContext;
import org.springframework.test.context.ActiveProfiles;
import static org.junit.jupiter.api.Assertions.*;

@ActiveProfiles({"rag", "rag-test"})
@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.NONE, properties = {
        "spring.datasource.url=jdbc:h2:mem:recovery-scheduling;MODE=PostgreSQL;DB_CLOSE_DELAY=-1",
        "app.chat.recovery-interval-ms=25"})
@DirtiesContext
class RecoverySchedulingTests {
    @Autowired private ChatStore store;
    @Autowired private JdbcTemplate jdbc;
    @Test void staleTurnRecoversWithoutAnyStoreCallWhileFreshAndCompletedStayUnchanged() throws Exception {
        var input = new Request("Recovery fixture", UUID.randomUUID(), null);
        var stale = store.accept(input);
        var fresh = store.accept(new Request("Fresh fixture", UUID.randomUUID(), null));
        var completed = store.accept(new Request("Completed fixture", UUID.randomUUID(), null));
        var answer = new MockAiClient("answered").query("Q");
        store.complete(completed, answer);
        jdbc.update("UPDATE chat_receipts SET created_at=? WHERE client_request_id IN (?,?)",
                Timestamp.from(Instant.now().minusSeconds(61)), input.clientRequestId(), completed.meta().clientRequestId());
        long deadline = System.nanoTime() + java.time.Duration.ofSeconds(5).toNanos();
        // Store calls also recover; JDBC-only polling proves the periodic task ran.
        while (!"failed".equals(state(input.clientRequestId())) && System.nanoTime() < deadline) { Thread.sleep(20); }
        assertEquals("failed", state(input.clientRequestId()));
        assertEquals("pending", state(fresh.meta().clientRequestId()));
        assertEquals("completed", state(completed.meta().clientRequestId()));
        assertEquals("PROCESSING_INTERRUPTED", jdbc.queryForObject(
                "SELECT error_code FROM chat_messages WHERE id=?", String.class, stale.meta().assistantMessageId()));
        assertEquals("completed", jdbc.queryForObject(
                "SELECT state FROM chat_messages WHERE id=?", String.class, stale.meta().userMessageId()));
        assertNull(store.complete(stale, answer));
        assertEquals(0, jdbc.queryForObject("SELECT COUNT(*) FROM chat_citations WHERE assistant_message_id=?",
                Integer.class, stale.meta().assistantMessageId()));
        var replay = assertThrows(ApiException.class, () -> store.accept(input));
        assertEquals(503, replay.status());
        assertEquals("PROCESSING_INTERRUPTED", replay.body().error().code());
        assertTrue(replay.body().error().retryable());
    }
    private String state(UUID id) {
        return jdbc.queryForObject("SELECT state FROM chat_receipts WHERE client_request_id=?", String.class, id);
    }
}
