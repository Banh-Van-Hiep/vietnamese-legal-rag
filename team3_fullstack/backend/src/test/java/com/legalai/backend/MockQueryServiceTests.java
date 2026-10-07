package com.legalai.backend;

import java.util.UUID;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.Executors;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicInteger;
import com.legalai.backend.ai.AiClient;
import com.legalai.backend.ai.MockAiClient;
import com.legalai.backend.ai.dto.ArticleResponse;
import com.legalai.backend.ai.dto.RagAnswer;
import com.legalai.backend.chat.ChatService;
import com.legalai.backend.chat.dto.ChatRequest;
import com.legalai.backend.common.exception.ApiException;
import com.legalai.backend.common.web.PageResponse.PageRequest;
import com.legalai.backend.conversation.ConversationService;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

class MockQueryServiceTests {
    @Test void pendingRequestBlocksReplayNewTurnAndDeletionWithoutHoldingStoreLock() throws Exception {
        var store = new ConversationService();
        UUID conversation = store.create("Test").conversation_id();
        var entered = new CountDownLatch(1);
        var release = new CountDownLatch(1);
        var calls = new AtomicInteger();
        AiClient ai = new AiClient() {
            public RagAnswer query(String question) {
                calls.incrementAndGet();
                entered.countDown();
                try {
                    if (!release.await(5, TimeUnit.SECONDS)) { throw new IllegalStateException("Test timed out"); }
                } catch (InterruptedException error) { Thread.currentThread().interrupt(); throw new IllegalStateException(error); }
                return new MockAiClient("answered").query(question);
            }
            public ArticleResponse article(String document, String article) { throw new UnsupportedOperationException(); }
        };
        var service = new ChatService(ai, store);
        var request = new ChatRequest(conversation, UUID.randomUUID(), "Test");
        try (var executor = Executors.newVirtualThreadPerTaskExecutor()) {
            var task = executor.submit(() -> service.query(request));
            try {
                assertTrue(entered.await(5, TimeUnit.SECONDS));
                var history = executor.submit(() -> store.messages(conversation, new PageRequest(0, 20))).get(2, TimeUnit.SECONDS);
                assertEquals("pending", history.items().get(1).state());
                var replay = assertThrows(ApiException.class, () -> service.query(request));
                assertEquals("REQUEST_IN_PROGRESS", replay.body().error().code());
                var busy = assertThrows(ApiException.class, () -> service.query(new ChatRequest(conversation, UUID.randomUUID(), "New")));
                assertEquals("CONVERSATION_BUSY", busy.body().error().code());
                assertEquals("CONVERSATION_BUSY", assertThrows(ApiException.class, () -> store.delete(conversation)).body().error().code());
            } finally { release.countDown(); }
            var response = task.get(5, TimeUnit.SECONDS);
            assertEquals(response, service.query(new ChatRequest(null, request.client_request_id(), "Test")));
            assertEquals(1, calls.get());
            assertEquals(2, store.messages(conversation, new PageRequest(0, 20)).total_elements());
        }
    }

    @Test void upstreamFailureIsSavedAndReplayedAsErrorInsteadOfInsufficientContext() {
        for (int status : new int[] {503, 504}) {
            var store = new ConversationService();
            var calls = new AtomicInteger();
            String code = status == 504 ? "UPSTREAM_TIMEOUT" : "SERVICE_UNAVAILABLE";
            AiClient ai = new AiClient() {
                public RagAnswer query(String question) {
                    calls.incrementAndGet();
                    throw new ApiException(status, code, "Dịch vụ tạm thời không phản hồi.", true);
                }
                public ArticleResponse article(String document, String article) { throw new UnsupportedOperationException(); }
            };
            var service = new ChatService(ai, store);
            var request = new ChatRequest(null, UUID.randomUUID(), "Test");
            var failure = assertThrows(ApiException.class, () -> service.query(request));
            assertEquals(status, failure.status());
            assertNotNull(failure.conversationId());
            var messages = store.messages(failure.conversationId(), new PageRequest(0, 20)).items();
            assertEquals("completed", messages.get(0).state());
            var assistant = messages.get(1);
            assertEquals("failed", assistant.state());
            assertNull(assistant.content());
            assertNull(assistant.answer_status());
            assertTrue(assistant.citations().isEmpty());
            assertEquals(code, assistant.error_code());
            assertEquals(failure, assertThrows(ApiException.class, () -> service.query(request)));
            assertEquals(1, calls.get());
            store.delete(failure.conversationId());
            assertEquals("REQUEST_NOT_FOUND", assertThrows(ApiException.class, () -> service.query(request)).body().error().code());
        }
    }
}
