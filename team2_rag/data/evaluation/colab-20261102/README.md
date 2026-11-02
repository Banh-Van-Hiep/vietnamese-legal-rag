# Bằng chứng Colab ngày 02/11/2026

- Code thực nghiệm: `1f51f66fa87166f23af32cf428226426a56a4b5c`, working tree sạch.
- 110 câu answered, 2.576 chunk; Tesla T4, không gọi LLM.
- Hai chính sách dùng cùng Hybrid top 20 và weights BGE. Chỉ đổi truncate;
  strict=True, không fallback, không sửa nội dung chunk.
- BGE gốc: 97/110 hoàn tất, 13 lỗi passage dài. BGE truncate: 110/110,
  không lỗi retrieval/rerank. Trạng thái `ERROR` của run là do lỗi nhánh gốc;
  không phải lỗi setup hoặc nhánh truncate.
- Golden gồm 40 câu `team2_reviewed`, 70 câu `draft_needs_legal_review`;
  chưa có split/gold groups, không coi là nghiệm thu Dev/Test.

`reranker-exploratory.json` và `.md` là output nguyên bản. ZIP còn giữ
Golden đầu vào, manifest, revision/framework/package metadata và kiểm tra
token độc lập. `cohort-summary.json` được tính offline từ raw, kèm hash
nguồn; tách toàn bộ 110 câu, 40 câu nhập cũ và 70 câu draft. Không phải một
lượt chạy model khác.

Đã kiểm tra hash code/corpus/Golden/manifest, pool và thứ tự theo điểm;
tính lại Recall/MRR độc lập khớp raw. Không lưu weights hoặc vector index.
Xem [báo cáo tác động](../../../../docs/team2_rag/reranker_impact_analysis.md).
