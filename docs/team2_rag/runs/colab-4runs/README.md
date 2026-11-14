# Kết quả benchmark RAG v2 trên Colab: 4 lượt (10/11/2026)

Nhãn: **exploratory** (Dev Set chưa đóng băng, Golden Phase 1 gồm 30 câu).

## Cấu hình

- Code: `develop` tại `3b307fa` (đã có prompt làm rõ `clause`/`point` null và claim phải có nguồn).
- Colab T4 GPU, `gemini-3.1-flash-lite`, không fallback.
- Hybrid BM25 + Qdrant Dense (`AITeamVN/Vietnamese_Embedding`), trọng số 0,5:1, `RAG_TOP_K=10`, rerank tắt, `LLM_MAX_CONTEXT_CHUNKS=10`.
- Nhóm A (`run1`, `run2`): `LLM_MAX_CONTEXT_CHARS=9000`. Nhóm B (`run3`, `run4`): `LLM_MAX_CONTEXT_CHARS=24000`.
- Notebook: `notebooks/rag_v2_benchmark_colab.ipynb` (nhánh `feature/team2-colab-benchmark`).
- Chi tiết môi trường: `run-settings.json`. Mỗi lượt có `rag_v2_benchmark_report.json/.md` do runner sinh ra và `execution.json`.

## Kết quả (tính lại từ `raw_results`)

| Lượt | Nhóm | Trả lời / lỗi | Coverage | Hallucination mức câu |
| :--- | :--- | :---: | :---: | :---: |
| run1 | A | 17 / 13 | 96,77% | 11,76% (2/17) |
| run2 | A | 27 / 3 | 96,67% | 11,11% (3/27) |
| run3 | B | 29 / 1 | 97,94% | 6,90% (2/29) |
| run4 | B | 30 / 0 | 98,02% | 6,67% (2/30) |

Citation Correctness 100% ở cả 4 lượt. Không câu nào bị từ chối. Hallucination mức câu chưa lượt nào đạt mục tiêu ≤5%.

## Giới hạn, đọc trước khi dùng số liệu

1. **run1 không dùng được để đo.** 13 câu đầu (gold_001 đến 012, 014) đều lỗi hạ tầng Gemini (timeout hoặc quá tải), nên mẫu chỉ còn 17 câu. 20 lỗi trong 4 lượt đều là lỗi hạ tầng, không phải lỗi prompt.
2. **Nhóm A và B gần như cùng context.** Dựng lại bằng `build_context`: ở 9000 ký tự LLM nhận trung bình 9,73 chunk, ở 24000 ký tự là 10. Hai nhóm chỉ khác nhau ở 3 câu (gold_019, gold_026, gold_027). Vì vậy chênh lệch Hallucination giữa hai nhóm chưa chứng minh 24000 ký tự tốt hơn; có thể chỉ là nhiễu và lỗi hạ tầng.
3. **`llm_context_chunk_ids` trong các file này là chunk được trích dẫn**, không phải chunk đã gửi cho LLM (chương trình thay context bằng bản chỉ còn chunk được trích sau khi nhận câu trả lời). Không dùng trường này để kết luận "LLM nhận đủ chunk đúng chưa". Runner đã sửa ở commit sau để lưu riêng chunk gửi (`llm_context_chunk_ids`) và chunk trích (`cited_chunk_ids`); các lượt sau mới có.
4. **Bộ kiểm là heuristic từ vựng.** Câu bị gắn hallucination lặp lại: gold_016 (4/4 lượt, chưa kiểm là sai thật hay báo nhầm), gold_002 (3/4, báo nhầm vì chunk nguồn chỉ có hai từ "1. Doanh nghiệp."), gold_026 (2/4, claim "nguồn không quy định" sai thật).
5. Chưa có số liệu dao động đủ lớn để kết luận tỷ lệ thật; mẫu 17 đến 30 câu.
