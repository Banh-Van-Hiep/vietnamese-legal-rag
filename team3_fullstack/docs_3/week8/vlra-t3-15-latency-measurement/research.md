# Research — T3-15

## Decisions

- **Locust2.43.1 + Python3.12**: lựa chọn Python Locust đã có trong nhiệm vụ tuần8; pin dependency của công cụ riêng, không đổi runtime sản phẩm. Module parser/report thuần Python để unit test không monkey patch. Entry point patch gevent trước networking.
- **Finite local runner**: Environment/LocalRunner, hàng đợi hữu hạn, mỗi sample được claim một lần; main greenlet đợi tất cả lượt đã claim kết thúc rồi quit. Warm-up chạy riêng.
- **Đo terminal SSE**: Locust native HTTP stream chỉ đo đến headers. Report dùng đồng hồ đơn điệu tới terminal và event SSE riêng; không cộng native HTTP với terminal thành hai request.
- **Deadline toàn lượt**: gevent.Timeout với exception riêng bao cả heartbeat liên tục; socket timeout riêng không đủ.
- **Trace log opt-in**: CHAT_LATENCY JSON, timing backend_init/ai_service/db_persist/stream và total_ms. Không thêm SSE/header/schema hoặc gọi Python ngoài AiClient. Pha chưa chạy=null; replay/outcome/error được phân biệt.
- **Official preconditions**: live cần split report T3-13 khớp hash Dev90 và upstream ready không đánh dấu mock; event timing phải gắn upstream origin đúng cấu hình. Đây không thay review pháp lý của bên bàn giao.
- **Metric boundary**: chat tới complete, article API tới JSON body đủ6 field. Report ghi rõ chưa đo render Viewer; không suy thời gian Retrieval/Rerank/LLM riêng từ HTTP chờ AI.
- **Output**: JSON có version1, giữ các field ví dụ nhiệm vụ tuần8; output độc quyền tạo mới. Không sửa file nguồn và không lưu question/answer/raw lỗi/đường dẫn cá nhân.

## Primary sources

- [Locust2.43.1 metadata](https://pypi.org/project/locust/2.43.1/).
- [Environment/LocalRunner lifecycle](https://docs.locust.io/en/2.43.1/use-as-lib.html).
- [HttpSession implementation — stream headers time](https://docs.locust.io/en/2.43.1/_modules/locust/clients.html).
- [Locust request events](https://docs.locust.io/en/2.43.1/extending-locust.html).
- [gevent total timeout](https://www.gevent.org/api/gevent.timeout.html).
- [gevent patching](https://www.gevent.org/api/gevent.monkey.html).

## Alternatives

k6/JMeter có trong lựa chọn task nhưng thêm runtime/DSL vào workflow hiện có. Stdlib-only
đơn giản hơn nhưng không đúng lựa chọn công cụ ghi trong nhiệm vụ. Không đổi stack RAG,
không merge nhánh Team2 hoặc sửa Article Store để chạy nghiệm thu.

Backend ApiRequestFilter tự cấp trace cho public request; không đòi echo X-Request-ID từ client. Entry point patch networking/queue nhưng giữ native thread locks (thread=False), tắt auto-patch lần hai của Locust; LocalRunner chỉ dùng greenlet.
