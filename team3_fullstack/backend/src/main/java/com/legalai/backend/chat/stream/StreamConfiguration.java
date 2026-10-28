package com.legalai.backend.chat.stream;

import java.util.Arrays;
import java.util.concurrent.ArrayBlockingQueue;
import java.util.concurrent.ScheduledThreadPoolExecutor;
import java.util.concurrent.ThreadPoolExecutor;
import java.util.concurrent.TimeUnit;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.context.annotation.Profile;
import org.springframework.core.env.Environment;

@Configuration
@Profile("rag")
public class StreamConfiguration {
    public StreamConfiguration(Environment env) {
        if (Arrays.asList(env.getActiveProfiles()).contains("mock")) {
            throw new IllegalStateException("Use rag or legacy mock, not both profiles");
        }
    }
    @Bean(destroyMethod = "shutdown")
    public ThreadPoolExecutor chatWorkers(@Value("${app.chat.workers:8}") int workers) {
        if (workers < 1 || workers > 64) { throw new IllegalArgumentException("Invalid chat worker limit"); }
        return new ThreadPoolExecutor(workers, workers, 0, TimeUnit.MILLISECONDS, new ArrayBlockingQueue<>(workers));
    }
    @Bean(destroyMethod = "shutdown")
    public ScheduledThreadPoolExecutor chatHeartbeats() {
        var scheduler = new ScheduledThreadPoolExecutor(1);
        scheduler.setRemoveOnCancelPolicy(true);
        return scheduler;
    }
}
