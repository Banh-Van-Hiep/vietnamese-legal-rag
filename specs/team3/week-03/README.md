# Tuần 3 — Bàn giao kiểm thử VLRA-28 và VLRA-29

**Bản biên bản:** v1.0, ngày 19/10/2026. **Source được kiểm tra:** `5a9af42e734391e00dfc0f7ede304506fdd5a28f`.
Đây là bộ hồ sơ bàn giao kiểm thử, còn lỗi và phần BLOCKED; không yêu cầu nghiệm thu toàn tuần.

| Cần xem | Tài liệu |
| --- | --- |
| Biên bản có thể tải | [PDF](reports/bien-ban-kiem-thu.pdf), [Word](reports/bien-ban-kiem-thu.docx) |
| Testcase và Input / Expected / Actual / Result | [Biên bản Markdown, mục III](reports/bien-ban-kiem-thu.md) — 26 nhóm ca, ánh xạ duy nhất 56 unittest |
| Tổng kết và chỉ số corpus | [Verification](verification.md), [CSV từng câu](evidence/bm25-cases.csv) |
| Unit / regression | [56 retrieval tests](evidence/unit-results.json), [JUnit](evidence/junit.xml), [81 regression tests](evidence/regression-results.json) |
| Người làm Dense | [D-01, D-02, D-03 và cách tái hiện](002-vlra-29-dense-hybrid-tests/issues.md) |
| Người làm Hybrid | [Bàn giao interface và điều kiện chạy](002-vlra-29-dense-hybrid-tests/hybrid-handoff.md) |
| Chạy lại sau sửa / phiên bản tiếp theo | [Retest và versioning](retest.md) |
| Phạm vi / task | [Requirements](requirements.md), [Tasks](tasks.md) |

Retrieval: **53 PASS / 3 FAIL**, không ERROR/SKIP. Full regression: **76 PASS / 3 FAIL /
2 ERROR**; hai ERROR preprocess đã tái hiện riêng, nằm ngoài retrieval. Dense model thật,
Qdrant server và Hybrid runtime chưa đủ điều kiện kiểm chứng. Oracle RRF không thay runtime.

Phần bàn giao mới chỉ gồm tests, công cụ đánh giá và hồ sơ tuần 3. Tài liệu/code Team 1/2, corpus,
contract, FE/BE và thay đổi tổ chức tài liệu đang dở được giữ ngoài phần bàn giao. Evidence lưu
nguyên snapshot lần chạy; các phát biểu “chưa commit/push” trong hồ sơ cũ mô tả thời
điểm kiểm thử trước khi người dùng yêu cầu xuất bản. Theo quyết định mới nhất, hồ sơ
được chia sẻ trực tiếp từ nhánh `feature/team3/tuan`; không tạo PR hoặc cập nhật Jira.
