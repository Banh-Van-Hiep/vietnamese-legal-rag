package com.legalai.backend.chat.stream;

import java.util.Map;
import java.util.UUID;
import java.util.concurrent.atomic.AtomicLong;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

class TurnTimingsTests {
    private static final UUID ID = UUID.fromString("44444444-4444-4444-8444-444444444444");

    @Test void measuresNonOverlappingPhasesAndResidualWithoutWallClock() {
        var clock = new AtomicLong(); var timing = new TurnTimings(clock::get);
        assertEquals("turn", timing.measure("backend_init", () -> { clock.set(1_000_000); return "turn"; }));
        clock.set(2_000_000);
        timing.measure("ai_service", () -> clock.set(7_000_000));
        timing.measure("db_persist", () -> clock.set(9_000_000));
        timing.measure("stream_finish", () -> clock.set(10_000_000));
        var row = timing.snapshot("trace", ID, "completed", "http://localhost:8001", true);
        assertEquals(10.0, row.get("total_ms"));
        assertEquals(Map.of("backend_init", 1.0, "ai_service", 5.0, "db_persist", 2.0, "stream_finish", 1.0), row.get("phases_ms"));
        assertEquals(ID.toString(), row.get("client_request_id"));
        assertEquals("trace", row.get("trace_id"));
        assertFalse(row.containsKey("question")); assertFalse(row.containsKey("answer"));
    }

    @Test void exceptionKeepsMeasuredDurationAndLeavesUnreachedPhaseNull() {
        var clock = new AtomicLong(); var timing = new TurnTimings(clock::get);
        var failure = new IllegalStateException("private");
        var actual = assertThrows(IllegalStateException.class, () -> timing.measure("ai_service", () -> {
            clock.set(3_000_000); throw failure;
        }));
        assertSame(failure, actual);
        var row = timing.snapshot("trace", ID, "failed", "http://localhost:8001", false);
        var phases = (Map<?, ?>) row.get("phases_ms");
        assertEquals(3.0, phases.get("ai_service")); assertNull(phases.get("db_persist"));
        assertFalse(row.toString().contains("private"));
        assertEquals(false, row.get("transport_connected"));
    }

    @Test void accumulatesSeparatedStreamWritesAndKeepsReplayDistinct() {
        var clock = new AtomicLong(); var timing = new TurnTimings(clock::get);
        timing.measure("stream_finish", () -> clock.set(1_000_000));
        clock.set(4_000_000);
        timing.measure("stream_finish", () -> clock.set(6_000_000));
        var row = timing.snapshot("trace", ID, "replayed", "http://localhost:8001", true);
        var phases = (Map<?, ?>) row.get("phases_ms");
        assertEquals(3.0, phases.get("stream_finish"));
        assertNull(phases.get("ai_service")); assertNull(phases.get("db_persist"));
        assertEquals("replayed", row.get("outcome"));
    }

    @Test void rejectsUnknownPhaseBeforeRunningOperation() {
        var ran = new AtomicLong(); var timing = new TurnTimings(() -> 0L);
        assertThrows(IllegalArgumentException.class, () -> timing.measure("unknown", () -> ran.incrementAndGet()));
        assertEquals(0, ran.get());
    }
}
