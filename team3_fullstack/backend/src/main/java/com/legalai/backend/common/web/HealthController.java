package com.legalai.backend.common.web;

import java.util.Map;
import com.legalai.backend.common.exception.ApiException;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@RestController
public class HealthController {
    @GetMapping("/api/v1/health")
    public Map<String, String> health(@RequestParam Map<String, String> parameters) {
        if (!parameters.isEmpty()) { throw ApiException.invalid(); }
        return Map.of("status", "up");
    }
}
