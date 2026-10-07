package com.legalai.backend.common.web;

import java.io.IOException;
import com.legalai.backend.common.exception.ApiException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.servlet.HandlerInterceptor;
import org.springframework.web.servlet.config.annotation.InterceptorRegistry;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurer;

@Configuration
public class ApiRequestInterceptor implements WebMvcConfigurer, HandlerInterceptor {
    @Override
    public void addInterceptors(InterceptorRegistry registry) {
        registry.addInterceptor(this).addPathPatterns("/api/v1/**");
    }

    @Override
    public boolean preHandle(HttpServletRequest request, HttpServletResponse response, Object handler) throws IOException {
        if (Boolean.TRUE.equals(request.getAttribute("payloadTooLarge"))) {
            throw new ApiException(413, "PAYLOAD_TOO_LARGE", "Nội dung yêu cầu vượt quá 16 KiB.", false);
        }
        if (!request.getMethod().equals("POST") && request.getInputStream().read() != -1) {
            throw ApiException.invalid();
        }
        return true;
    }
}
