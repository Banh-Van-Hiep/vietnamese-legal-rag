# Kế Hoạch Triển Khai Kỹ Thuật — Tuần 8
## Phân Hệ: Fullstack & System (Team 3)

---

## 1. Thông Tin Chung & Mục Tiêu Trọng Tâm
- **Giai đoạn:** Tuần 8 (Quy đổi học phần: Tuần 5 cũ + 3 = Tuần 8 mới).
- **Mục tiêu trọng tâm:**
  - Thiết lập kịch bản kiểm thử tải và đo đạc độ trễ toàn trình (End-to-End Latency Measurement: p50, p95) từ lúc Frontend gửi request đến khi nhận complete event.
  - Thực hiện kiểm thử đồng thời (Concurrency Test) với tải trọng tiêu chuẩn của đồ án: **5 người dùng đồng thời (5 concurrent sessions)** trên tối thiểu 50 truy vấn hợp lệ để kiểm tra tính ổn định của connection pool và thread pool.
  - Giám sát tính tương thích ngược (Backward Compatibility) của API Contract khi Team 1 và Team 2 nâng cấp lên Retrieval v2 và Reranker tối ưu.
  - Hỗ trợ công cụ tự động hóa runner và thu thập log hiệu năng tập trung theo `X-Request-ID`.

---

## 2. Bảng Phân Rã Công Việc (Task Breakdown)

| Mã Task | Tên công việc & Nội dung | Tiêu chí hoàn thành (Definition of Done - DoD) |
| :--- | :--- | :--- |
| **VLRA-T3-15** | **Thiết lập Kịch bản Đo đạc Độ trễ Toàn trình (Latency Measurement)**<br>- Lập trình script đo thời gian tự động (sử dụng k6, JMeter hoặc Python Locust).<br>- Ghi nhận chi tiết thời gian tiêu tốn qua từng pha: Backend khởi tạo lượt $\rightarrow$ AI Service xử lý $\rightarrow$ DB commit $\rightarrow$ Stream hoàn tất.<br>- Đo đạc các chỉ số: p50, p90, p95, p99 trên bộ câu hỏi Dev Set. | - Báo cáo `latency_report_week8.json` ghi nhận đầy đủ các mốc phân vị.<br>- Xác nhận độ trễ p95 của toàn hệ thống nằm trong ngân sách cho phép: p95 $\le 45$ giây đối với câu hỏi Live và p95 $\le 1$ giây đối với thao tác xem Điều luật. |
| **VLRA-T3-16** | **Kiểm thử Xử lý Đồng thời (Concurrency Test - 5 Users)**<br>- Chạy kịch bản 5 người dùng gửi câu hỏi đồng thời trên 5 hội thoại khác nhau.<br>- Kiểm tra tính ổn định của cơ chế cấp phát tài nguyên: HikariCP connection pool trên PostgreSQL, ThreadPoolTaskExecutor phục vụ `SseEmitter`.<br>- Kiểm tra xem có trường hợp nào bị rò rỉ kết nối (connection leak) hoặc treo vĩnh viễn không. | - Tỷ lệ request thành công đạt 100% khi chạy tải 5 người dùng đồng thời.<br>- Không có hiện tượng cạn kiệt connection pool (`ConnectionPoolTimeoutException`).<br>- Background recovery giải phóng chuẩn xác nếu có lượt bị timeout. |
| **VLRA-T3-17** | **Giám sát Tính Tương thích Khi Nâng Cấp Retrieval v2**<br>- Phối hợp với Team 1 nạp thử nghiệm các candidate từ Retrieval v2.<br>- Đảm bảo toàn bộ 12 trường dữ liệu của ứng viên và 6 trường của Article Store không bị thay đổi kiểu dữ liệu hoặc tên trường.<br>- Đảm bảo Backend Java mapping thông suốt mà không cần sửa code controller. | - Kiểm thử hồi quy (Regression Test) pass 100% khi chuyển sang Retrieval v2.<br>- Public API giữ nguyên tính ổn định tuyệt đối cho phía Frontend React. |
| **VLRA-T3-18** | **Tối ưu hóa Hiệu năng Frontend & Cải thiện Trải nghiệm Stream**<br>- Tối ưu hóa việc re-render trên React khi nhận liên tục các event `delta`.<br>- Bổ sung hiển thị thời gian phản hồi (Latency badge) trên giao diện dành cho môi trường debug.<br>- Thử nghiệm trải nghiệm người dùng trên các điều kiện mạng chậm (Simulated Slow Network 3G). | - Giao diện không bị giật lag (frame drop) khi text stream về liên tục.<br>- Xử lý ngắt kết nối an toàn khi người dùng bấm nút "Dừng nhận". |

---

## 3. Thiết Kế Kiến Trúc, State Machine & Luồng SSE Frame

### 3.1. Sơ Đồ Phân Bổ Ngân Sách Thời Gian Toàn Trình (End-to-End Latency Budget)
Theo quy định tại mục 3.2 của Baseline v2.0 (NFR-06 đến NFR-09):
```
Tổng Ngân Sách Deadline AI = 45 Giây
├─ 1. Backend đón nhận & DB Transaction khởi tạo:  <= 0.5s
├─ 2. Mạng Backend -> AI Service (Local HTTP):      <= 0.1s
├─ 3. Tầng AI Service & Retrieval (Team 1 & 2):    <= 43.0s
│   ├─ Query Rewrite & Preprocess:                <= 0.5s
│   ├─ Retrieval Team 1 (BM25 + Qdrant + RRF):    <= 1.0s (p95)
│   ├─ Cross-Encoder Reranker (bge-reranker-m3):  <= 3.5s
│   ├─ LLM Generation (Gemini / OpenAI):          <= 30.0s
│   └─ Citation Validation & JSON Parsing:        <= 1.0s
├─ 4. Backend Persist DB & Commit:                 <= 0.4s
└─ 5. Phát stream Delta & Complete về Frontend:     <= 1.0s
────────────────────────────────────────────────────────────────────
Ngưỡng Timeout Cấu Hình:
- Backend chờ AI Service:  readTimeout = 50 giây (dự phòng thêm 5s)
- Frontend chờ Backend:    fetchTimeout = 60 giây
- Background Recovery:     Hủy và giải phóng lượt treo sau 60 giây
```

### 3.2. Cấu Hình Pool Kết Nối & Threading Backend (Spring Boot Config)
```properties
# Cấu hình HikariCP tối ưu cho 5-10 người dùng đồng thời
spring.datasource.hikari.maximum-pool-size=15
spring.datasource.hikari.minimum-idle=5
spring.datasource.hikari.idle-timeout=30000
spring.datasource.hikari.connection-timeout=5000

# Cấu hình Async Thread Pool cho SSE Emitter
spring.task.execution.pool.core-size=10
spring.task.execution.pool.max-size=20
spring.task.execution.pool.queue-capacity=50
```

---

## 4. Đặc Tả Hợp Đồng & Mock Data

### 4.1. Cấu Trúc Báo Cáo Đo Đạc Hiệu Năng Tuần 8
```json
{
  "test_id": "PERF-CONCURRENCY-5U-50Q",
  "concurrency_level": 5,
  "total_requests": 50,
  "successful_requests": 50,
  "failed_requests": 0,
  "latency_distribution_seconds": {
    "min": 4.2,
    "p50": 16.8,
    "p90": 24.5,
    "p95": 28.2,
    "max": 33.1
  },
  "phases_breakdown_p95_seconds": {
    "backend_init": 0.08,
    "retrieval_t1": 0.72,
    "reranker_t2": 2.45,
    "llm_generation": 22.3,
    "db_persist": 0.15
  },
  "system_metrics": {
    "max_memory_mb": 512,
    "db_connections_peak": 7,
    "status": "HEALTHY_AND_COMPLIANT"
  }
}
```

### 4.2. Khung SSE Frame Báo Sự Cố Timeout (Khi vượt quá deadline)
Trong trường hợp AI Service bị treo quá 50 giây, Backend chủ động ngắt và phát frame lỗi an toàn về giao diện:
```http
event: error
data: {"error":{"code":"UPSTREAM_TIMEOUT","message":"Hệ thống xử lý AI vượt quá thời gian tối đa (45 giây). Vui lòng thử lại câu hỏi của bạn.","retryable":true}}

```

---

## 5. Ma Trận Phụ Thuộc Liên Team (Inter-team Dependencies)

| Chiều phối hợp | Hạng mục bàn giao | Mục đích sử dụng | Định dạng / Kênh giao tiếp |
| :--- | :--- | :--- | :--- |
| **Team 3 $\rightarrow$ Team 1 & Team 2** | - Báo cáo phân tích độ trễ thực tế qua từng pha (`phases_breakdown_p95`).<br>- Cảnh báo các ca truy vấn có thời gian vượt ngưỡng 35 giây. | Team 1 và Team 2 tập trung tối ưu hóa các điểm nghẽn hiệu năng (bottlenecks) trong pipeline truy hồi và prompt. | Báo cáo hiệu năng tuần 8. |
| **Team 1 $\rightarrow$ Team 3 (Retrieval)** | - Bản phát hành Retrieval v2 để kiểm thử hồi quy trên môi trường staging của Backend. | Team 3 xác nhận API Contract của thư viện không bị thay đổi và chạy ổn định. | Python library update. |
| **Team 2 $\rightarrow$ Team 3 (AI Service)** | - Báo cáo thời gian chạy của Reranker và token usage tương ứng. | Team 3 theo dõi và đối soát chi phí token cùng độ trễ mạng giữa các container Docker. | Log trace theo `X-Request-ID`. |

## 6. Kết quả kiểm chứng hiện hành

Đối chiếu từng task/DoD và phần còn thiếu tại [verification.md](verification.md), ngày 28/10/2026.
Không suy hoàn thành từ kế hoạch hoặc từ số test PASS; mock và live được kết luận riêng.
