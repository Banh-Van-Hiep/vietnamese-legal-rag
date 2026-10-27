package com.legalai.backend;

import java.nio.charset.StandardCharsets;
import java.sql.Timestamp;
import java.time.Instant;
import java.util.List;
import java.util.UUID;
import java.util.concurrent.CyclicBarrier;
import java.util.concurrent.Executors;
import java.util.concurrent.TimeUnit;
import com.legalai.backend.ai.MockAiClient;
import com.legalai.backend.ai.dto.RagAnswer;
import com.legalai.backend.chat.stream.StreamDtos.Request;
import com.legalai.backend.common.exception.ApiException;
import com.legalai.backend.conversation.persistence.ChatStore;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.core.io.ClassPathResource;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.jdbc.datasource.DriverManagerDataSource;
import org.springframework.jdbc.datasource.DataSourceTransactionManager;
import org.springframework.jdbc.datasource.init.ResourceDatabasePopulator;
import static org.junit.jupiter.api.Assertions.*;

class ChatStoreTests {
    private ChatStore store;
    private JdbcTemplate jdbc;
    private DriverManagerDataSource source;
    private final RagAnswer answer = new MockAiClient("answered").query("Q");
    @BeforeEach void setup() {
        source = dataSource();
        var init = new ResourceDatabasePopulator(new ClassPathResource("db/chat-schema.sql"));
        init.setSqlScriptEncoding(StandardCharsets.UTF_8.name()); init.execute(source);
        jdbc = new JdbcTemplate(source);
        store = new ChatStore(jdbc, new DataSourceTransactionManager(source));
    }
    protected DriverManagerDataSource dataSource() {
        return new DriverManagerDataSource("jdbc:h2:mem:" + UUID.randomUUID() + ";MODE=PostgreSQL;DB_CLOSE_DELAY=-1", "sa", "");
    }
    private Request request(Long conv) { return new Request("Câu hỏi", UUID.randomUUID(), conv); }
    @Test void firstQuestionTitleIsBoundedUnicodeAndSurvivesReplayFollowupAndReload() {
        String firstQuestion = "\u00a0Điều kiện\n  thành lập doanh nghiệp " + "😀".repeat(100);
        String normalized = "Điều kiện thành lập doanh nghiệp " + "😀".repeat(100);
        String expected = normalized.substring(0, normalized.offsetByCodePoints(0, 100));
        var input = new Request(firstQuestion, UUID.randomUUID(), null);
        var turn = store.accept(input);
        long id = turn.meta().conversationId();
        assertEquals(expected, store.conversation(id).title());
        assertEquals(100, expected.codePointCount(0, expected.length()));
        assertEquals(firstQuestion, store.messages(id).getFirst().content());
        store.complete(turn, answer);
        store.accept(input); // Replay must not change the title or duplicate the turn.
        var followup = store.accept(new Request("Câu hỏi tiếp theo", UUID.randomUUID(), id));
        store.complete(followup, answer);
        var fresh = new ChatStore(jdbc, new DataSourceTransactionManager(source));
        assertEquals(expected, fresh.conversation(id).title());
        assertEquals(expected, fresh.conversations().stream().filter(c -> c.id() == id).findFirst().orElseThrow().title());
        assertEquals(4, fresh.messages(id).size());
    }
    @Test void emptyDefaultConversationTakesFirstAcceptedQuestionEvenIfRagFails() {
        long id = store.create("Hội thoại mới").id();
        var input = new Request("Cần bao nhiêu vốn?", UUID.randomUUID(), id);
        var turn = store.accept(input);
        store.fail(turn, new ApiException(503, "SERVICE_UNAVAILABLE", "Tạm thời không sẵn sàng.", true));
        assertCode("SERVICE_UNAVAILABLE", () -> store.accept(input));
        var retry = store.accept(new Request("Câu hỏi khác", UUID.randomUUID(), id));
        store.complete(retry, answer);
        assertEquals("Cần bao nhiêu vốn?", store.conversation(id).title());
    }
    @Test void customAndExistingNonemptyTitlesArePreserved() {
        long custom = store.create("Thủ tục doanh nghiệp").id();
        store.complete(store.accept(request(custom)), answer);
        assertEquals("Thủ tục doanh nghiệp", store.conversation(custom).title());
        var oldTurn = store.accept(request(null));
        long existing = oldTurn.meta().conversationId();
        store.complete(oldTurn, answer);
        // Simulate a conversation saved before the title decision; no automatic migration.
        jdbc.update("UPDATE chat_conversations SET title='Hội thoại mới' WHERE id=?", existing);
        store.complete(store.accept(request(existing)), answer);
        assertEquals("Hội thoại mới", store.conversation(existing).title());
        var whitespace = store.accept(new Request("\u00a0", UUID.randomUUID(), null));
        assertEquals("Hội thoại mới", store.conversation(whitespace.meta().conversationId()).title());
    }
    @Test void persistsPairReplaysWithAnotherRepositoryAndStableTimestamp() {
        var request = request(null);
        var turn = store.accept(request);
        assertEquals(2, store.messages(turn.meta().conversationId()).size());
        assertEquals("pending", store.messages(turn.meta().conversationId()).getLast().state());
        var complete = store.complete(turn, answer);
        var fresh = new ChatStore(jdbc, new DataSourceTransactionManager(source));
        assertEquals(complete, fresh.accept(request).replay());
        assertEquals(complete.createdAt(), fresh.messages(complete.conversationId()).getLast().createdAt());
        assertEquals(1, jdbc.queryForObject("SELECT COUNT(*) FROM chat_citations", Integer.class));
        assertEquals(complete, fresh.accept(new Request(request.question(), request.clientRequestId(), complete.conversationId())).replay());
    }
    @Test void pendingConflictBusyAndFailureReplayDoNotAddMessages() {
        var input = request(null);
        var turn = store.accept(input);
        assertCode("REQUEST_IN_PROGRESS", () -> store.accept(input));
        assertCode("REQUEST_ID_CONFLICT", () -> store.accept(new Request("Other", input.clientRequestId(), null)));
        assertCode("REQUEST_ID_CONFLICT", () -> store.accept(new Request(input.question(), input.clientRequestId(), 999L)));
        assertCode("CONVERSATION_BUSY", () -> store.accept(request(turn.meta().conversationId())));
        assertCode("CONVERSATION_BUSY", () -> store.delete(turn.meta().conversationId()));
        store.fail(turn, new ApiException(504, "UPSTREAM_TIMEOUT", "Hết thời gian.", true));
        var replay = assertThrows(ApiException.class, () -> store.accept(input));
        assertEquals(504, replay.status());
        assertEquals("UPSTREAM_TIMEOUT", replay.body().error().code());
        assertEquals("failed", store.messages(turn.meta().conversationId()).getLast().state());
        assertEquals(2, store.messages(turn.meta().conversationId()).size());
    }
    @Test void historyOnlyAnsweredPairsAtMostFiveInChronologicalOrder() {
        Long conv = null;
        for (int i = 0; i < 7; i++) {
            var turn = store.accept(new Request("Q" + i, UUID.randomUUID(), conv));
            conv = turn.meta().conversationId(); store.complete(turn, answer);
        }
        var insufficient = store.accept(request(conv));
        store.complete(insufficient, new RagAnswer("insufficient_context", "Thiếu căn cứ", List.of()));
        var failed = store.accept(request(conv));
        store.fail(failed, new ApiException(500, "INTERNAL_ERROR", "Lỗi", false));
        var next = store.accept(request(conv));
        assertEquals(10, next.history().size());
        assertEquals("Q2", next.history().getFirst().content());
        assertEquals("Q6", next.history().get(8).content());
        for (int i=0;i<10;i++) { assertEquals(i%2 == 0 ? "user" : "assistant", next.history().get(i).role()); }
    }
    @Test void historyBudgetUsesCodepointsAndDropsWholeOldestPairs() {
        Long conv = null;
        String longAnswer = "😀".repeat(9990) + " [C1]";
        for (int i=0;i<3;i++) {
            var turn = store.accept(new Request("Q" + i, UUID.randomUUID(), conv));
            conv = turn.meta().conversationId();
            store.complete(turn, new RagAnswer("answered", longAnswer, answer.citations()));
        }
        var history = store.accept(request(conv)).history();
        assertEquals(4, history.size());
        assertEquals("Q1", history.getFirst().content());
        assertTrue(history.stream().mapToInt(m -> m.content().codePointCount(0,m.content().length())).sum() <= 20000);
    }
    @Test void recoveryFailsStaleTurnAndRejectsLateResult() {
        var input = request(null); var turn = store.accept(input);
        jdbc.update("UPDATE chat_receipts SET created_at=? WHERE client_request_id=?", Timestamp.from(Instant.now().minusSeconds(61)), input.clientRequestId());
        store.recover();
        assertCode("PROCESSING_INTERRUPTED", () -> store.accept(input));
        assertNull(store.complete(turn, answer));
        assertEquals("failed", store.messages(turn.meta().conversationId()).getLast().state());
        assertEquals(0, jdbc.queryForObject("SELECT COUNT(*) FROM chat_citations", Integer.class));
    }
    @Test void deleteRemovesContentAndKeepsOnlyTombstone() {
        var input = request(null); var turn = store.accept(input); store.complete(turn, answer);
        store.delete(turn.meta().conversationId());
        assertCode("REQUEST_NOT_FOUND", () -> store.accept(input));
        assertCode("CONVERSATION_NOT_FOUND", () -> store.messages(turn.meta().conversationId()));
        for (String table : List.of("chat_conversations","chat_messages","chat_citations")) {
            assertEquals(0, jdbc.queryForObject("SELECT COUNT(*) FROM " + table, Integer.class));
        }
        var row = jdbc.queryForMap("SELECT * FROM chat_receipts WHERE client_request_id=?", input.clientRequestId());
        for (String key : List.of("fingerprint","response_snapshot","error_snapshot","logical_status")) { assertNull(row.get(key)); }
        assertNotNull(row.get("deleted_at"));
        assertNull(store.complete(turn, answer));
    }
    @Test void duplicateFirstRequestsAcrossRepositoryInstancesCreateOnePair() throws Exception {
        var second = new ChatStore(jdbc, new DataSourceTransactionManager(source));
        var input = request(null); var barrier = new CyclicBarrier(2);
        try (var pool = Executors.newFixedThreadPool(2)) {
            var a = pool.submit(() -> race(store,input,barrier)); var b = pool.submit(() -> race(second,input,barrier));
            String one = a.get(5, TimeUnit.SECONDS), two = b.get(5, TimeUnit.SECONDS);
            assertTrue((one.equals("accepted") && two.equals("REQUEST_IN_PROGRESS")) || (two.equals("accepted") && one.equals("REQUEST_IN_PROGRESS")), one + "/" + two);
        }
        assertEquals(1, jdbc.queryForObject("SELECT COUNT(*) FROM chat_conversations", Integer.class));
        assertEquals(2, jdbc.queryForObject("SELECT COUNT(*) FROM chat_messages", Integer.class));
    }
    @Test void failedResultTransactionRollsBackAllRows() {
        var turn = store.accept(request(null));
        jdbc.update("ALTER TABLE chat_citations ADD CONSTRAINT test_reject CHECK (citation_id <> 'C1')");
        assertThrows(org.springframework.dao.DataAccessException.class, () -> store.complete(turn, answer));
        assertEquals("pending", store.messages(turn.meta().conversationId()).getLast().state());
        assertEquals("pending", jdbc.queryForObject("SELECT state FROM chat_receipts", String.class));
        assertEquals(0, jdbc.queryForObject("SELECT COUNT(*) FROM chat_citations", Integer.class));
    }
    @Test void failedAcceptanceDoesNotLeaveReceipt() {
        assertCode("CONVERSATION_NOT_FOUND", () -> store.accept(request(999L)));
        assertEquals(0, jdbc.queryForObject("SELECT COUNT(*) FROM chat_receipts", Integer.class));
    }
    @Test void differentRequestsForSameConversationAcrossInstancesAllowOnlyOnePending() throws Exception {
        long conv = store.create("Concurrent conversation").id();
        var second = new ChatStore(jdbc, new DataSourceTransactionManager(source));
        var barrier = new CyclicBarrier(2);
        try (var pool = Executors.newFixedThreadPool(2)) {
            var a = pool.submit(() -> race(store,request(conv),barrier));
            var b = pool.submit(() -> race(second,request(conv),barrier));
            var outcomes = List.of(a.get(5,TimeUnit.SECONDS),b.get(5,TimeUnit.SECONDS));
            assertTrue(outcomes.contains("accepted")); assertTrue(outcomes.contains("CONVERSATION_BUSY"));
        }
        assertEquals(2,store.messages(conv).size());
        assertEquals(1,jdbc.queryForObject("SELECT COUNT(*) FROM chat_receipts",Integer.class));
    }
    @Test void queryAndDeleteShareDatabaseLock() throws Exception {
        long conv = store.create("Delete race").id();
        var barrier = new CyclicBarrier(2);
        try (var pool = Executors.newFixedThreadPool(2)) {
            var accept = pool.submit(() -> race(store,request(conv),barrier));
            var delete = pool.submit(() -> {
                barrier.await();
                try { store.delete(conv); return "deleted"; }
                catch (ApiException e) { return e.body().error().code(); }
            });
            String a = accept.get(5,TimeUnit.SECONDS), d = delete.get(5,TimeUnit.SECONDS);
            assertTrue(a.equals("accepted") && d.equals("CONVERSATION_BUSY")
                    || a.equals("CONVERSATION_NOT_FOUND") && d.equals("deleted"),a+"/"+d);
        }
    }
    @Test void terminalStateCannotBeOverwrittenAndPendingConstraintIsDatabaseOwned() {
        var turn = store.accept(request(null));
        assertThrows(org.springframework.dao.DataAccessException.class, () -> jdbc.update(
                "UPDATE chat_messages SET pending_conversation_id=NULL WHERE id=?",turn.meta().assistantMessageId()));
        var complete = store.complete(turn,answer);
        assertNull(store.fail(turn,new ApiException(500,"INTERNAL_ERROR","Lỗi",false)));
        assertNull(store.complete(turn,answer));
        assertEquals(complete,store.accept(new Request(turn.question(),turn.meta().clientRequestId(),null)).replay());
    }
    @Test void completedReplayWaitsForDeleteLockAndDoesNotReturnDeletedSnapshot() throws Exception {
        var input=request(null); var turn=store.accept(input); store.complete(turn,answer);
        var started=new java.util.concurrent.CountDownLatch(1);
        var pending=new java.util.concurrent.atomic.AtomicReference<java.util.concurrent.Future<ChatStore.Turn>>();
        try (var pool=Executors.newSingleThreadExecutor()) {
            new org.springframework.transaction.support.TransactionTemplate(new DataSourceTransactionManager(source)).executeWithoutResult(tx -> {
                jdbc.queryForObject("SELECT id FROM chat_conversations WHERE id=? FOR UPDATE",Long.class,turn.meta().conversationId());
                pending.set(pool.submit(() -> { started.countDown(); return store.accept(input); }));
                try {
                    assertTrue(started.await(2,TimeUnit.SECONDS));
                    assertThrows(java.util.concurrent.TimeoutException.class,() -> pending.get().get(200,TimeUnit.MILLISECONDS));
                } catch (InterruptedException e) { Thread.currentThread().interrupt(); throw new IllegalStateException(e); }
                jdbc.update("UPDATE chat_receipts SET state='deleted',fingerprint=NULL,response_snapshot=NULL,error_snapshot=NULL,logical_status=NULL,deleted_at=? WHERE client_request_id=?",
                        Timestamp.from(Instant.now()),input.clientRequestId());
                jdbc.update("DELETE FROM chat_conversations WHERE id=?",turn.meta().conversationId());
            });
            var error=assertThrows(java.util.concurrent.ExecutionException.class,() -> pending.get().get(5,TimeUnit.SECONDS));
            assertInstanceOf(ApiException.class,error.getCause());
            assertEquals("REQUEST_NOT_FOUND",((ApiException)error.getCause()).body().error().code());
        }
    }
    private String race(ChatStore target, Request input, CyclicBarrier barrier) throws Exception {
        barrier.await();
        try { target.accept(input); return "accepted"; } catch (ApiException e) { return e.body().error().code(); }
    }
    private void assertCode(String code, org.junit.jupiter.api.function.Executable action) {
        assertEquals(code, assertThrows(ApiException.class, action).body().error().code());
    }
}
