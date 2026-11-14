package com.legalai.backend.conversation.persistence;

import java.util.concurrent.CountDownLatch;
import java.util.concurrent.ScheduledThreadPoolExecutor;
import java.util.concurrent.TimeUnit;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.Mockito.*;

class ChatRecoveryTests {
    @Test void transientFailureDoesNotCancelSubsequentTicks() throws Exception {
        var store = mock(ChatStore.class);
        var succeeded = new CountDownLatch(1);
        doThrow(new IllegalStateException("transient fixture"))
                .doAnswer(call -> { succeeded.countDown(); return null; }).when(store).recover();
        var executor = new ScheduledThreadPoolExecutor(1);
        var recovery = new ChatRecovery(store, executor, 10);
        try {
            recovery.start();
            assertTrue(succeeded.await(3, TimeUnit.SECONDS));
            verify(store, atLeast(2)).recover();
        } finally { recovery.stop(); executor.shutdownNow(); }
    }
    @Test void repeatedStartupCreatesOneScheduleAndShutdownCancelsIt() {
        var executor = new ScheduledThreadPoolExecutor(1);
        executor.setRemoveOnCancelPolicy(true);
        var recovery = new ChatRecovery(mock(ChatStore.class), executor, 60000);
        try {
            recovery.start(); recovery.start();
            assertEquals(1, executor.getQueue().size());
            recovery.stop();
            assertTrue(executor.getQueue().isEmpty());
        } finally { recovery.stop(); executor.shutdownNow(); }
    }
}
