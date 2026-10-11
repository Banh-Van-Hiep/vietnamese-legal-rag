package com.legalai.backend.common.web;

import java.util.List;
import java.util.Map;
import org.springframework.util.MultiValueMap;
import com.legalai.backend.common.exception.ApiException;

public record PageResponse<T>(List<T> items, int page, int size, long total_elements, long total_pages) {
    public record PageRequest(int page, int size) {
        public static PageRequest parse(MultiValueMap<String, String> parameters) {
            if (!parameters.keySet().stream().allMatch(k -> k.equals("page") || k.equals("size"))) {
                throw ApiException.invalid();
            }
            return new PageRequest(integer(parameters, "page", 0, 0, Integer.MAX_VALUE),
                    integer(parameters, "size", 20, 1, 100));
        }

        private static int integer(Map<String, List<String>> parameters, String key, int fallback, int min, int max) {
            if (!parameters.containsKey(key)) { return fallback; }
            List<String> values = parameters.get(key);
            if (values.size() != 1 || !values.getFirst().matches("[0-9]+")) { throw ApiException.invalid(); }
            try {
                int value = Integer.parseInt(values.getFirst());
                if (value < min || value > max) { throw ApiException.invalid(); }
                return value;
            } catch (NumberFormatException error) { throw ApiException.invalid(); }
        }
    }

    public static <T> PageResponse<T> of(List<T> all, PageRequest request) {
        int start = (int) Math.min((long) request.page() * request.size(), all.size());
        int end = (int) Math.min((long) start + request.size(), all.size());
        return new PageResponse<>(List.copyOf(all.subList(start, end)), request.page(), request.size(),
                all.size(), (all.size() + (long) request.size() - 1) / request.size());
    }
}
