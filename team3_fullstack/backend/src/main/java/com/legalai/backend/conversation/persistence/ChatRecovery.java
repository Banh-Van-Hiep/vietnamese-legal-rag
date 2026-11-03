package com.legalai.backend.conversation.persistence;

import java.util.concurrent.ScheduledFuture;
import java.util.concurrent.ScheduledThreadPoolExecutor;
import java.util.concurrent.TimeUnit;
import jakarta.annotation.PreDestroy;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.context.event.ApplicationReadyEvent;
import org.springframework.context.annotation.Profile;
import org.springframework.context.event.EventListener;
import org.springframework.stereotype.Component;

/** Recovers idle stale turns independently of request traffic and SSE heartbeats. */
@Component
@Profile("rag")
public class ChatRecovery {
    private static final Logger LOG = LoggerFactory.getLogger(ChatRecovery.class);
    private final ChatStore store;
    private final ScheduledThreadPoolExecutor scheduler;
    private final long intervalMs;
    private ScheduledFuture<?> task;
    public ChatRecovery(ChatStore store,
            @Qualifier("chatRecoveryScheduler") ScheduledThreadPoolExecutor scheduler,
            @Value("${app.chat.recovery-interval-ms:30000}") long intervalMs) {
        if (intervalMs < 1) { throw new IllegalArgumentException("Invalid recovery interval"); }
        this.store = store; this.scheduler = scheduler; this.intervalMs = intervalMs;
    }
    @EventListener(ApplicationReadyEvent.class)
    public synchronized void start() {
        if (task == null) {
            task = scheduler.scheduleWithFixedDelay(this::recover, intervalMs, intervalMs, TimeUnit.MILLISECONDS);
        }
    }
    private void recover() {
        try { store.recover(); }
        catch (RuntimeException failure) {
            LOG.warn("Pending-turn recovery failed: {}", failure.getClass().getSimpleName());
        }
    }
    @PreDestroy
    public synchronized void stop() {
        if (task != null) { task.cancel(false); }
    }
}
