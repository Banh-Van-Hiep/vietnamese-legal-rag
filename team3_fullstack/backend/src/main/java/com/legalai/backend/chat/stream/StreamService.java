package com.legalai.backend.chat.stream;

import java.io.IOException;
import java.util.Map;
import java.util.concurrent.Semaphore;
import java.util.concurrent.ScheduledThreadPoolExecutor;
import java.util.concurrent.ThreadPoolExecutor;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.RejectedExecutionException;
import com.legalai.backend.ai.AiClient;
import com.legalai.backend.ai.AiResponseValidator;
import com.legalai.backend.chat.stream.StreamDtos.*;
import com.legalai.backend.common.exception.ApiException;
import com.legalai.backend.conversation.persistence.ChatStore;
import com.legalai.backend.conversation.persistence.ChatStore.Turn;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.context.annotation.Profile;
import org.springframework.dao.DataAccessException;
import org.springframework.http.MediaType;
import org.springframework.stereotype.Service;
import org.springframework.web.servlet.mvc.method.annotation.SseEmitter;
import tools.jackson.databind.json.JsonMapper;

@Service
@Profile("rag")
public class StreamService {
    private static final Logger LOG = LoggerFactory.getLogger(StreamService.class);
    private final ChatStore store;
    private final AiClient ai;
    private final ThreadPoolExecutor workers;
    private final ScheduledThreadPoolExecutor scheduler;
    private final Semaphore slots;
    private final long heartbeatMs;
    private final JsonMapper json = JsonMapper.builder().build();
    public record Accepted(Turn turn, SseEmitter emitter) { }
    public StreamService(ChatStore store, AiClient ai, @Qualifier("chatWorkers") ThreadPoolExecutor workers,
            @Qualifier("chatHeartbeats") ScheduledThreadPoolExecutor scheduler, @Value("${app.chat.workers:8}") int count,
            @Value("${app.chat.heartbeat-ms:10000}") long heartbeatMs) {
        this.store = store; this.ai = ai; this.workers = workers; this.scheduler = scheduler;
        this.slots = new Semaphore(count); this.heartbeatMs = heartbeatMs;
        if (heartbeatMs < 1) { throw new IllegalArgumentException("Invalid heartbeat interval"); }
    }
    public Accepted open(Request request, String trace) {
        // Resolve idempotency/busy before admission so pool saturation cannot bypass their contract.
        Turn turn = store.accept(request);
        if (!slots.tryAcquire()) {
            if (turn.replay() == null) { store.fail(turn, unavailable()); }
            throw unavailable().inNumericConversation(turn.meta().conversationId());
        }
        var session = new Session(new SseEmitter(55000L));
        try { workers.execute(() -> run(turn, session, trace)); }
        catch (RejectedExecutionException e) {
            slots.release();
            if (turn.replay() == null) { store.fail(turn, unavailable()); }
            throw unavailable().inNumericConversation(turn.meta().conversationId());
        }
        return new Accepted(turn, session.emitter);
    }
    private void run(Turn turn, Session session, String trace) {
        session.event("meta", turn.meta());
        var heartbeat = scheduler.scheduleAtFixedRate(session::heartbeat, heartbeatMs, heartbeatMs, TimeUnit.MILLISECONDS);
        try {
            Complete response = turn.replay();
            if (response == null) {
                var answer = AiResponseValidator.query(ai.query(turn.question(), turn.history(), trace));
                response = store.complete(turn, answer);
                if (response == null) {
                    LOG.info("Discarded late RAG result requestId={}", trace);
                    var failure = store.fail(turn, new ApiException(503, "PROCESSING_INTERRUPTED",
                            "Lượt xử lý đã bị gián đoạn.", true));
                    if (failure != null) { session.terminal("error", failure.body()); }
                    return;
                }
            }
            if ("answered".equals(response.status())) { session.event("delta", Map.of("text", response.answer())); }
            session.terminal("complete", response);
        } catch (RuntimeException e) {
            ApiException failure = e instanceof ApiException a ? a
                    : e instanceof DataAccessException ? persistence()
                    : new ApiException(500, "INTERNAL_ERROR", "Hệ thống gặp lỗi khi xử lý yêu cầu.", false);
            try {
                ApiException stored = store.fail(turn, failure);
                if (stored != null) { session.terminal("error", stored.body()); }
            } catch (DataAccessException db) {
                // State is uncertain. Keep the UUID for reconciliation; never emit complete.
                session.terminal("error", persistence().body());
            }
            LOG.warn("Chat failed requestId={} code={}", trace, failure.body().error().code());
        } finally {
            heartbeat.cancel(false);
            slots.release();
            session.finish();
        }
    }
    private static ApiException unavailable() {
        return new ApiException(503, "SERVICE_UNAVAILABLE", "Dịch vụ đang bận, vui lòng thử lại sau.", true);
    }
    private static ApiException persistence() {
        return new ApiException(503, "PERSISTENCE_UNAVAILABLE", "Không thể lưu kết quả hội thoại.", true);
    }
    /** Serializes heartbeat/result writes; transport failures never mutate database state. */
    private final class Session {
        private final SseEmitter emitter;
        private boolean connected = true;
        private boolean terminal;
        Session(SseEmitter emitter) {
            this.emitter = emitter;
            emitter.onCompletion(this::disconnected);
            emitter.onError(e -> disconnected());
            emitter.onTimeout(this::disconnected);
        }
        synchronized void disconnected() { connected = false; }
        synchronized void event(String name, Object data) {
            if (!connected || terminal) { return; }
            try { emitter.send(SseEmitter.event().name(name).data(json.writeValueAsString(data), MediaType.APPLICATION_JSON)); }
            catch (IOException | IllegalStateException e) { connected = false; }
        }
        synchronized void heartbeat() {
            if (!connected || terminal) { return; }
            try { emitter.send(SseEmitter.event().comment("heartbeat")); }
            catch (IOException | IllegalStateException e) { connected = false; }
        }
        synchronized void terminal(String name, Object data) { event(name, data); terminal = true; }
        synchronized void finish() {
            if (connected) { emitter.complete(); connected = false; }
        }
    }
}
