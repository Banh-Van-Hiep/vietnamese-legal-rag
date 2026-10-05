# VLRA-11 — Quy chuẩn trích dẫn

Nguồn chuẩn: [rag_response.schema.json](../../contracts/v0.1/rag_response.schema.json).
Không thêm claim/quote/snippet/document_number/metadata hiệu lực vào v0.1.

## Tạo citation

Team 2 gán C1…Cn cho chunk trong context. Model chỉ trả marker/ID đã dùng;
Team 2 sao chép metadata từ bảng nguồn, không để LLM sinh lại.

| Field | Nguồn |
| --- | --- |
| citation_id | Nhãn C1…C10 do Team 2 gán cho lượt |
| chunk_id, document_id, article_id | Giữ nguyên định danh candidate |
| document_title, article | Nhãn hiển thị từ candidate |
| clause, point | Sao chép, giữ null |
| source_url | HTTPS URL từ candidate |

Không suy số hiệu/ngày ban hành từ document_id.
Giữ ID Team 1 như bl-45-2019-qh14-v1__dieu-113__k1__0.
Metadata bổ sung để đề xuất v0.2 riêng.

## Marker/hiển thị

Nhận định pháp lý có marker ngay sau nội dung được hỗ trợ: "… [C1]."
Một nguồn có thể lặp marker nhiều lần nhưng list chỉ có một citation/chunk.
Không marker mồ côi/citation thừa; ID và chunk_id trong list phải duy nhất.
Sau khi chọn nguồn đã dùng, ID không nhất thiết liên tục.

Nhãn đề xuất: [C1] <document_title> — <article>, <clause>, <point>, bỏ nhãn null.
Team 3 có thể render số 1 nhưng phải giữ mapping C1.
Không đổi RagResponse sang camelCase/thêm snippet theo UI mock.
Viewer dùng document_id/article_id; nguồn gốc dùng source_url.
Đây là bàn giao thiết kế, không sửa frontend Team 3.

## Verification

1. Validate Draft 2020-12 và FormatChecker.
2. answered có nguồn; insufficient_context citations rỗng, không marker.
3. Parse mọi token dạng [C...]; chỉ C1…C10 hợp lệ.
4. Tập marker = tập citation_id; không ID/chunk_id trùng.
5. Nguồn thuộc context thực sự đã gửi LLM, không chỉ thuộc retrieval pool.
6. Mọi metadata khớp đúng candidate, kể cả null.
7. Review nguồn có hỗ trợ nội dung, điều kiện và ngoại lệ không.

Bước 1–6 chỉ chứng minh cấu trúc/provenance, không bảo đảm đúng ngữ nghĩa.
Week 2 đánh giá thủ công groundedness/coverage; chưa có verifier ngữ nghĩa.
Schema không tự kiểm tra mapping marker/context.

## Khi sai

JSON/shape sai → INVALID_LLM_OUTPUT; nguồn/marker/metadata sai → CITATION_INVALID.
Không âm thầm bỏ citation rồi giữ kết luận không nguồn; không sửa ID bằng suy đoán.
Thiếu căn cứ hợp lệ → insufficient_context. Không dùng thiếu căn cứ để che lỗi xử lý.
