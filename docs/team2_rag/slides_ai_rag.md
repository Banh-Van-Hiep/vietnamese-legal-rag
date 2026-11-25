---
marp: true
lang: vi
---

# Bài toán và vai trò Team 2

**VLRA-T2-50 · Phần AI và RAG**

- Hỏi đáp pháp luật doanh nghiệp, có căn cứ để mở đúng Điều luật.
- Team 2: điều phối RAG, sinh câu trả lời, kiểm trích dẫn.
- Thiếu căn cứ → nói rõ giới hạn hoặc từ chối.

Nguồn: [I/O](rag-io-specification.md), [Prompt](prompt-design.md).

---

# Kiến trúc pipeline

**Retrieval Team 1 → BGE tùy chọn → Context Builder**

**→ Prompt → Gemini → Kiểm citation / verification → Team 3**

- B0: BM25-only; T0: Hybrid + BGE.
- Chọn nguyên chunk; BGE lỗi thì lùi về thứ hạng Retrieval.
- B0/T0 đổi cả truy xuất và rerank: chưa tách riêng lợi ích BGE.

Nguồn: [Cấu hình G5](g5_b0_vs_t0_report.json), [Phân tích lỗi](g5_error_analysis.md).

---

# Chống bịa trích dẫn

- Chỉ kết luận từ `LEGAL CONTEXT`; giữ điều kiện, ngoại lệ.
- `[Ck]` phải khớp citation và metadata của chunk nguồn.
- Sai JSON / citation → chặn lỗi; không tự vá nhãn hoặc nguồn.
- Kiểm claim từ vựng là bước tùy chọn, chưa bảo đảm đúng ngữ nghĩa.

Nguồn: [Prompt](prompt-design.md), [Citation](citation-specification.md), [Giới hạn kiểm chứng](g5_error_analysis.md).

---

# G5: kết quả định lượng

| Chỉ số | B0 | T0 |
| :--- | ---: | ---: |
| Tổng số câu | 77 | 77 |
| `answered` / `error` | 60 / 1 | 61 / 1 |
| Citation correctness | 100,00% | 100,00% |
| Citation coverage | 99,17% | 100,00% |
| Hallucination theo câu, ước lượng từ vựng | 1,67% | 0,00% |

Nguồn bảng: [G5 Markdown](g5_b0_vs_t0_report.md), [JSON](g5_b0_vs_t0_report.json). Chất lượng loại câu lỗi khỏi mẫu số.

---

# Chấm mù và lỗi chính

**40 câu · 2 giám khảo · Điểm trung bình /10**

| | B0 | T0 |
| :--- | ---: | ---: |
| Có tính ca timeout | 8,80 | 9,04 |

Nguồn bảng và mẫu chấm: [Báo cáo chấm mù](g5_blind_evaluation_report.md).

- Context thiếu khoản; prompt từ chối nhầm; model trích sai.
- T0 vẫn có ca mất căn cứ; 3 câu BGE lỗi lùi về Hybrid.

Nguồn lỗi: [Phân tích lỗi G5](g5_error_analysis.md).

---

# Giới hạn và hướng tiếp

- Test Set 77 câu còn `draft_needs_legal_review`; cần rà soát pháp lý.
- NFR-07: p95 **19,330 s**, mới đo BM25-only.
- Timeout **45/50/60 s**; **1 chạy + 4 chờ**; **12 request/phút**.
- Đo Hybrid + BGE, hàng đợi và Java/UI; kiểm ngữ nghĩa sâu hơn.

Nguồn: [G5](g5_b0_vs_t0_report.md), [Nhãn](../../team1_data/golden/test_set_v1.json), [NFR](ai_service_load_and_stability_report.md), [Hàng đợi](ui-integration-guide.md), [Giới hạn gọi](../../team2_rag/docs_2/week12/tasks.md).
