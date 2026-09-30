# External LLM Provider Proposal

## Deployment Direction

Team 2 dự kiến dùng External LLM API, không chạy local LLM. Đây là hướng thiết kế cần được xác nhận về bảo mật, chi phí và deployment trước khi triển khai. Không provider/model nào được xem là tốt nhất khi chưa benchmark.

```text
Team 3 Backend / orchestration
          |
          v
       LLM Service
        /       \
OpenAI Provider  Gemini Provider
          |
          v
    External LLM API
```

LLM Service định nghĩa abstraction nội bộ; provider adapters triển khai lời gọi tương ứng sau này. Backend gọi service/provider qua server-side boundary. Frontend không được gọi trực tiếp provider. API key được nạp từ `.env`/secret store ở môi trường chạy, không hard-code và không commit `.env`.

## Proposed Input and Output

- **Input:** LLM Input gồm trusted system instruction, structured legal context có nguồn, user question và output instruction; xem [`schemas/llm_input.schema.json`](schemas/llm_input.schema.json).
- **Output:** answer tiếng Việt và citations có tham chiếu các chunk trong context; xem [`schemas/llm_output.schema.json`](schemas/llm_output.schema.json). Team 2 xác minh citation trước khi tạo RAG response.

## Errors, Timeout and Retry

Contract lỗi bên ngoài được mô tả tại [`schemas/error_response.schema.json`](schemas/error_response.schema.json). Thiết kế vận hành nên phân biệt cấu hình/authentication, rate limit, timeout, provider unavailable và invalid provider response; trả thông báo an toàn, không lộ secret hoặc raw sensitive provider payload.

Timeout và retry policy cần cấu hình theo provider, có giới hạn tổng thời gian và số lần thử. Chỉ retry lỗi tạm thời (ví dụ rate limit/transient server failure) với backoff và jitter; không retry lỗi validation/authentication không thể khắc phục. Phải tránh retry vô hạn và ghi nhận khi fallback/retry thất bại. Các ngưỡng cụ thể chưa được chốt.

## Cost and Latency Tracking

Thiết kế telemetry nên ghi provider/model/version, thời điểm, latency, token usage nếu provider trả về, retry count, outcome và cost estimate nếu có pricing metadata. Không ghi API key; hạn chế lưu raw prompt/context và áp dụng chính sách dữ liệu của project. Đơn vị/nguồn pricing, retention và privacy policy cần được xác nhận.

## Provider/Model Benchmark Proposal

So sánh OpenAI Provider và Gemini Provider trên cùng bộ câu hỏi, context, prompt version và tiêu chí chấm. Theo dõi answer quality, groundedness, citation validity/accuracy, latency p50/p95, lỗi, token usage và cost. Ghi model/version, cấu hình, ngày benchmark và điều kiện thử nghiệm; review cả tác động downstream. Chưa tuyên bố model hoặc provider nào tốt nhất khi chưa có kết quả benchmark có thể tái lập.

## Week 1 Status

Đây là proposal kiến trúc và vận hành; chưa có SDK, provider adapter, API key, LLM call hoặc benchmark implementation.