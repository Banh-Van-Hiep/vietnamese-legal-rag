package com.legalai.backend.common.exception;

import java.util.UUID;

public class ApiException extends RuntimeException {
    private final int status;
    private final ApiError body;
    private final UUID conversationId;

    public ApiException(int status, String code, String message, boolean retryable) {
        this(status, code, message, retryable, null);
    }

    public ApiException(int status, String code, String message, boolean retryable, UUID conversationId) {
        super(message);
        this.status = status;
        this.body = new ApiError(new ApiError.Detail(code, message, retryable));
        this.conversationId = conversationId;
    }

    public int status() { return status; }
    public ApiError body() { return body; }
    public UUID conversationId() { return conversationId; }

    public ApiException inConversation(UUID id) {
        return new ApiException(status, body.error().code(), getMessage(), body.error().retryable(), id);
    }

    public static ApiException invalid() {
        return new ApiException(400, "INVALID_REQUEST", "Dữ liệu yêu cầu không hợp lệ.", false);
    }
}
