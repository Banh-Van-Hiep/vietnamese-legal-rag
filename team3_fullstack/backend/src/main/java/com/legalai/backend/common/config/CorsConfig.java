package com.legalai.backend.common.config;

import java.net.URI;
import java.util.Arrays;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.servlet.config.annotation.CorsRegistry;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurer;

@Configuration
public class CorsConfig implements WebMvcConfigurer {
    private final String[] origins;

    public CorsConfig(@Value("${app.cors.allowed-origins}") String origins) {
        this.origins = Arrays.stream(origins.split(",", -1)).map(String::trim).distinct().toArray(String[]::new);
        for (String origin : this.origins) {
            if (!validOrigin(origin)) {
                throw new IllegalArgumentException("CORS_ALLOWED_ORIGINS must contain explicit http(s) origins without paths or wildcards");
            }
        }
    }

    private static boolean validOrigin(String value) {
        try {
            URI origin = URI.create(value);
            return ("http".equals(origin.getScheme()) || "https".equals(origin.getScheme()))
                    && origin.getHost() != null && origin.getUserInfo() == null
                    && origin.getRawPath().isEmpty() && origin.getRawQuery() == null && origin.getRawFragment() == null
                    && (origin.getPort() == -1 || (origin.getPort() >= 1 && origin.getPort() <= 65535));
        } catch (IllegalArgumentException error) { return false; }
    }

    @Override
    public void addCorsMappings(CorsRegistry registry) {
        registry.addMapping("/api/v1/**")
                .allowedOrigins(origins)
                .allowedMethods("GET", "POST", "DELETE", "OPTIONS")
                .allowedHeaders("Content-Type", "Accept", "X-Request-ID")
                .exposedHeaders("X-Request-ID", "X-Conversation-ID", "Location")
                .maxAge(3600);
    }
}
