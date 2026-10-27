# Research decisions — 19/10/2026

- Dùng unittest, baseline 18 BM25/22 Dense; thay kiểm tra generic trùng bằng mixin, giữ hành vi riêng. Không viết lại retriever.
- Evaluator nhận retrieve(question, top_k), constructor adapter CLI tách khỏi metric để Hybrid owner cắm factory sau. Không viết runtime Hybrid giả.
- JSON schema kèm ID uniqueness/rank/finiteness/provenance; schema PASS không chứng minh relevance.
- Golden baseline giữ nguyên; supplement và nhóm sidecar ở specs Team 3, giữ định dạng T2. Dùng validator T2 và kiểm cấu trúc độc lập vì validator không trả exit code lỗi.
- Model thật dùng AITeamVN/Vietnamese_Embedding; pin commit; fake vector chỉ chứng minh cơ chế. Thiếu tài nguyên/server ghi BLOCKED/NOT RUN.
- RRF oracle dùng Fraction theo proposal; công thức không thay runtime. Public K50 khác candidate100 nội bộ, bàn giao owner VLRA-27.
- Source review chỉ là rủi ro; xác nhận bằng test trước khi ghi defect. Kiểm norm overflow, prefix mismatch, point trùng, query shape và manifest hash.
- Đánh giá chỉ corpus-relative: không xác minh hiệu lực pháp lý; legal_status cấp văn bản không chứng minh unit applicability C5.
