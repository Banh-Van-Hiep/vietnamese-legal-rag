package com.legalai.backend.common.exception;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.ResponseEntity;
import org.springframework.http.MediaType;
import org.springframework.web.HttpMediaTypeNotAcceptableException;
import org.springframework.web.HttpMediaTypeNotSupportedException;
import org.springframework.web.HttpRequestMethodNotSupportedException;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;
import org.springframework.http.converter.HttpMessageNotReadableException;
import org.springframework.web.servlet.NoHandlerFoundException;
import org.springframework.web.servlet.resource.NoResourceFoundException;

@RestControllerAdvice
public class GlobalExceptionHandler {
    private static final Logger LOG = LoggerFactory.getLogger(GlobalExceptionHandler.class);

    @ExceptionHandler(ApiException.class)
    public ResponseEntity<ApiError> api(ApiException error) {
        var response = ResponseEntity.status(error.status()).contentType(MediaType.APPLICATION_JSON);
        if (error.conversationId() != null) {
            response.header("X-Conversation-ID", error.conversationId().toString());
        }
        return response.body(error.body());
    }

    @ExceptionHandler(HttpMessageNotReadableException.class)
    public ResponseEntity<ApiError> unreadable() { return api(ApiException.invalid()); }

    @ExceptionHandler(HttpMediaTypeNotSupportedException.class)
    public ResponseEntity<ApiError> mediaType() {
        return api(new ApiException(415, "UNSUPPORTED_MEDIA_TYPE", "Yêu cầu phải dùng application/json.", false));
    }

    @ExceptionHandler(HttpMediaTypeNotAcceptableException.class)
    public ResponseEntity<ApiError> notAcceptable() {
        return api(new ApiException(406, "NOT_ACCEPTABLE", "API trả dữ liệu application/json.", false));
    }

    @ExceptionHandler(HttpRequestMethodNotSupportedException.class)
    public ResponseEntity<ApiError> method(HttpRequestMethodNotSupportedException error) {
        var response = ResponseEntity.status(405).contentType(MediaType.APPLICATION_JSON);
        if (error.getSupportedMethods() != null) {
            response.header("Allow", String.join(", ", error.getSupportedMethods()));
        }
        return response.body(new ApiError(new ApiError.Detail("METHOD_NOT_ALLOWED", "Phương thức HTTP không được hỗ trợ.", false)));
    }

    @ExceptionHandler({NoResourceFoundException.class, NoHandlerFoundException.class})
    public ResponseEntity<ApiError> notFound() {
        return api(new ApiException(404, "NOT_FOUND", "Không tìm thấy API được yêu cầu.", false));
    }

    @ExceptionHandler(Exception.class)
    public ResponseEntity<ApiError> unexpected(Exception error) {
        LOG.error("Unhandled API error", error);
        return api(new ApiException(500, "INTERNAL_ERROR", "Hệ thống gặp lỗi khi xử lý yêu cầu.", false));
    }
}
