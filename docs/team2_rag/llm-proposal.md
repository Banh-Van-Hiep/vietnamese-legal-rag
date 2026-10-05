# VLRA-11 — Đề xuất LLM cho demo

Ngày đối chiếu tài liệu chính chủ: 05/10/2026. Chưa benchmark tiếng Việt pháp lý.
So sánh đúng bốn lựa chọn của task; model minh họa cụ thể không có nghĩa là mới nhất.

## So sánh

| Model cụ thể | Tiếng Việt/độ chính xác dự kiến | JSON/citation | Chi phí và triển khai |
| --- | --- | --- | --- |
| GPT-4o (API gpt-4o) | Ứng viên baseline tổng quát; chưa có điểm luật lao động của dự án | Có Structured Outputs; vẫn kiểm tra marker và nội dung | API trả phí, $2.50 input / $10 output cho 1M text token |
| Gemini 2.5 Flash | Ứng viên API để đối chiếu; chưa có bằng chứng cùng bộ test để kết luận hơn/kém GPT-4o | Có structured outputs, vẫn cần validation | $0.30 input / $2.50 output (gồm thinking) cho 1M token; quyền truy cập 2.5 bị giới hạn với tài khoản đã dùng trước |
| Qwen2.5-7B-Instruct | Model card nêu hỗ trợ tiếng Việt; chưa chứng minh chính xác luật lao động | Có cải tiến instruction/JSON nhưng không bảo đảm citation đúng | Open weights; tự host cần compute/vận hành, giá API tùy provider |
| PhoGPT-4B-Chat | Pretrain đơn ngữ tiếng Việt, phù hợp đối chứng về văn phong; không suy ra giỏi luật hơn | Cần thử tuân thủ prompt/JSON; chưa xác nhận cơ chế structured-output cho deployment | Open weights; có chi phí máy/vận hành, không có mức API chung |

Các nhận xét phù hợp là suy luận thiết kế, không phải xếp hạng độ chính xác đã đo.
Cả bốn model đều có thể hallucinate. Không chọn bằng kiến thức luật nhớ sẵn;
đánh giá khả năng trả lời đúng theo context và từ chối khi thiếu nguồn.

## Quyết định thiết kế

- Chính: GPT-4o API cho baseline demo, vì đã xác minh structured output và không cần host LLM.
- Dự phòng để đánh giá/thay cấu hình: Gemini 2.5 Flash, chỉ khi tài khoản project có quyền
  truy cập. Tài liệu Google hiện giới hạn 2.5 với người đã dùng; không mặc định tài khoản mới dùng được.
  Nếu không có quyền, review model Gemini khác và cập nhật giá/model ID trước tích hợp.
- Qwen/PhoGPT là đối chứng, không host local trong scope Week 1 và không yêu cầu Team 3
  thêm hạ tầng. Không chạy model nặng trên máy thành viên chỉ để hoàn tất tài liệu.
- Không tự gọi cả hai provider hoặc fallback trả phí trong một request. Đổi provider qua
  cấu hình được team phê duyệt, giữ nguyên RagResponse v0.1.

Chọn GPT-4o không phải khẳng định tốt nhất hoặc model mới nhất; lợi ích dự kiến là
triển khai baseline nhanh. Review chi phí, quyền truy cập và privacy trước Week 2.
OpenAI Docs giúp xác nhận giá/Structured Outputs, không cung cấp kết quả luật lao động
để tự chấm điểm tiếng Việt.

## Ước tính chi phí

Standard paid text, không cache/batch/tool; không dùng free tier làm cơ sở vận hành.
Giả định một lượt 4000 input token và 500 output token:

| Model | Phép tính USD/lượt | USD/1000 lượt |
| --- | --- | ---: |
| GPT-4o | (4000 × 2.50 + 500 × 10) / 1,000,000 = 0.015 | 15.00 |
| Gemini 2.5 Flash | (4000 × 0.30 + 500 × 2.50) / 1,000,000 = 0.00245 | 2.45 |

Gemini giả định 500 là toàn bộ output bị tính tiền, kể cả thinking nếu có;
không chỉ tính text hiển thị. Tokenization giữa provider khác nhau, đây là kịch bản
ước tính, không phải hóa đơn thực tế. Chưa gồm reranker, server, retry, thuế hoặc storage.
Open weights không có nghĩa inference miễn phí: tự host tính thời gian máy và vận hành;
hosted Qwen/PhoGPT phải lấy bảng giá đúng nhà cung cấp/region/model.

## Prompt, lỗi và thời gian

Input: [system instruction + legal context + question](prompt-design.md).
Output model nội bộ: status/answer/used_citation_ids; Team 2 dựng citation từ nguồn.
Provider schema có thể chỉ hỗ trợ subset Draft 2020-12: validate đầy đủ sau khi nhận.
Model refusal/truncated/invalid JSON là lỗi, không đưa như câu trả lời pháp luật.

AI deadline 45 giây theo Team 3. Ngân sách khởi đầu: retrieval 5 giây,
rerank tối đa 5 giây, packing/verification 5 giây, một LLM call tối đa 30 giây
và luôn bị giới hạn bởi thời gian còn lại. Không retry/fallback tự động ở MVP.
Timeout → LLM_TIMEOUT; unavailable/rate limit → LLM_UNAVAILABLE;
JSON sai → INVALID_LLM_OUTPUT; citation sai → CITATION_INVALID.
Backend sở hữu public HTTP mapping, request deduplication và persistence.

Gọi API server-side. Không commit keys, không gửi secrets/PII không cần thiết,
không log raw prompt/history mặc định. Corpus và mock query không chứa dữ liệu cá nhân.
Chỉ thống nhất provider/model khi team đã review chính sách dữ liệu và budget.

## Đánh giá Week 2

Bộ thử nhỏ 20 câu (đề xuất, chưa thu thập): 10 có căn cứ, 5 cần điều kiện/ngoại lệ,
5 thiếu context/ngoài corpus. Gán nguồn và câu trả lời mong đợi với người review.
Cùng prompt/context và output budget; ghi model snapshot, date, cấu hình, token usage.
Đánh giá: tiếng Việt 0–2 (khó hiểu/hiểu được/rõ), correctness và giữ điều kiện 0–2,
groundedness/coverage, provenance invalid count, từ chối đúng và latency/cost.
Ngưỡng thử nghiệm: không marker/ID giả vượt verifier; mọi câu thiếu căn cứ phải từ chối,
không bỏ điều kiện quan trọng. Không tuyên bố con số độ chính xác trước khi chạy.
Cần labeled corpus Team 1; benchmark không chặn việc hoàn thành bản thiết kế Week 1.

## Nguồn chính chủ

- [GPT-4o model/pricing/Structured Outputs](https://developers.openai.com/api/docs/models/gpt-4o)
- [Gemini pricing](https://ai.google.dev/gemini-api/docs/pricing)
- [Gemini 2.5 Flash và điều kiện truy cập](https://ai.google.dev/gemini-api/docs/models/gemini-2.5-flash)
- [Gemini structured output](https://ai.google.dev/gemini-api/docs/structured-output)
- [Qwen2.5-7B-Instruct model card](https://huggingface.co/Qwen/Qwen2.5-7B-Instruct)
- [PhoGPT-4B-Chat model card](https://huggingface.co/vinai/PhoGPT-4B-Chat)

Giá/quyền truy cập có thể thay đổi, kiểm tra lại trước khi chạy. Không đăng ký,
gọi API trả phí hoặc benchmark trong PR tài liệu này.
