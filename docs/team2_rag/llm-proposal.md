# LLM Proposal

## So sánh cho demo luật lao động

Bảng dùng model cụ thể để tránh so sánh tên cả họ model. Khả năng tiếng Việt/JSON dưới đây dựa trên tài liệu nhà phát hành; **chưa có benchmark độ chính xác pháp luật của dự án**, chưa xếp hạng chất lượng.

| Model | Tiếng Việt và output | Chi phí/vận hành | Đề xuất |
| --- | --- | --- | --- |
| GPT-4o | Hỗ trợ structured output; chưa đo độ đúng và grounding pháp luật tiếng Việt | API: $2.50 input / $10 output mỗi 1M token | Lựa chọn thử đầu tiên nếu có API/budget |
| Gemini 2.5 Flash | Hỗ trợ structured output; cần đo tiếng Việt với cùng prompt/context | API: $0.30 input / $2.50 output mỗi 1M token; output gồm thinking | Phương án so chi phí nếu tài khoản được truy cập |
| Qwen2.5-7B-Instruct | Model card nêu tiếng Việt và cải thiện JSON; chưa đo luật lao động | Open weights; chi phí máy chạy/hosting và vận hành, không coi là miễn phí | Để so sánh khi có tài nguyên |
| PhoGPT-4B-Chat | Model tiếng Việt; chưa có bằng chứng đáp ứng citation/JSON và độ đúng pháp luật của dự án | Open weights; cần máy chạy/hosting và vận hành | Để so sánh, chưa dùng mặc định |

Giá API text standard trả phí đối chiếu ngày 05/10/2026; không gồm thuế, retry, cache hay dịch vụ khác. Với 4000 input và 500 output token tính phí: GPT-4o khoảng $0.015/lượt, Gemini 2.5 Flash khoảng $0.00245/lượt. Thinking token có thể tăng chi phí Gemini; kiểm tra lại giá và quyền truy cập trước triển khai. Google hiện giới hạn model 2.5 cho tài khoản đã dùng trước đó; không mặc nhiên coi là lựa chọn dùng được cho tài khoản mới.

## Quyết định Week 1

Đề xuất API server-side GPT-4o để thử trước, Gemini là phương án cần đánh giá riêng. Không tự chuyển provider khi lỗi; Qwen/PhoGPT chưa cần triển khai local. Frontend không giữ API key hoặc gọi provider.

Trong ngân sách AI layer 45 giây theo Team 3, proposal ban đầu: retrieval tối đa 5 giây, rerank 5 giây, LLM tối đa 30 giây và 5 giây cho xử lý còn lại. Mỗi bước dùng thời gian còn lại, không cộng các timeout độc lập vượt tổng. Trước benchmark không bật retry mặc định; nếu bổ sung retry, phải giới hạn trong ngân sách này.

Output theo [I/O](rag-io-specification.md), luôn qua kiểm tra citation; API structured output không đảm bảo câu trả lời đúng pháp luật. Timeout/unavailable/output sai dùng mã lỗi Team 3 đã mô tả.

## Đánh giá sau khi có implementation

Dùng cùng bộ 20 câu luật lao động: 10 câu có nguồn trả lời, 5 câu có điều kiện/ngoại lệ, 5 câu thiếu căn cứ hoặc ngoài corpus. Người review chấm độ đúng tiếng Việt, bám nguồn, giữ điều kiện và citation support; đo thêm JSON hợp lệ, latency và chi phí thực. Đây là kế hoạch, không phải kết quả đã chạy.

## Nguồn chính thức

- [GPT-4o: model, structured output và giá](https://developers.openai.com/api/docs/models/gpt-4o)
- [Gemini 2.5 Flash: khả năng và quyền truy cập](https://ai.google.dev/gemini-api/docs/models/gemini-2.5-flash), [giá API](https://ai.google.dev/gemini-api/docs/pricing)
- [Qwen2.5-7B-Instruct model card](https://huggingface.co/Qwen/Qwen2.5-7B-Instruct)
- [PhoGPT-4B-Chat model card](https://huggingface.co/vinai/PhoGPT-4B-Chat)
