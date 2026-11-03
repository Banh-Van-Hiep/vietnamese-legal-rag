package com.legalai.backend.chat.stream;

import java.util.LinkedHashMap;
import java.util.Map;
import java.util.UUID;
import java.util.function.LongSupplier;
import java.util.function.Supplier;

/** Durations only: no wall-clock arithmetic, messages, citations or credentials. */
final class TurnTimings {
    private final LongSupplier clock;
    private final long started;
    private final Map<String, Double> phases = new LinkedHashMap<>();

    TurnTimings() { this(System::nanoTime); }
    TurnTimings(LongSupplier clock) {
        this.clock = clock; this.started = clock.getAsLong();
        for (String phase : new String[]{"backend_init", "ai_service", "db_persist", "stream_finish"}) {
            phases.put(phase, null);
        }
    }
    <T> T measure(String phase, Supplier<T> action) {
        if (!phases.containsKey(phase)) { throw new IllegalArgumentException("Unknown timing phase"); }
        long start = clock.getAsLong();
        try { return action.get(); }
        finally {
            double elapsed = (clock.getAsLong() - start) / 1_000_000.0;
            Double before = phases.get(phase);
            phases.put(phase, (before == null ? 0 : before) + elapsed);
        }
    }
    void measure(String phase, Runnable action) {
        measure(phase, () -> { action.run(); return null; });
    }
    Map<String, Object> snapshot(String trace, UUID request, String outcome, String upstream, boolean connected) {
        var row = new LinkedHashMap<String, Object>();
        row.put("kind", "chat"); row.put("trace_id", trace); row.put("client_request_id", request.toString());
        row.put("outcome", outcome); row.put("upstream_origin", upstream);
        row.put("phases_ms", new LinkedHashMap<>(phases));
        row.put("total_ms", (clock.getAsLong() - started) / 1_000_000.0);
        row.put("transport_connected", connected);
        return row;
    }
}
