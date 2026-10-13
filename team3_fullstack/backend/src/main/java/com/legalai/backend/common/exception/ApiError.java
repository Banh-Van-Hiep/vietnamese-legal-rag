package com.legalai.backend.common.exception;

public record ApiError(Detail error) {
    public record Detail(String code, String message, boolean retryable) { }
}
