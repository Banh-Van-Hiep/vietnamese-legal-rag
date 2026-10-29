# Data model — Golden split

Input: list150 object; bắt buộc id/question/expected_status/ground_truth/gold_chunk_ids/
citation/category/author; các chuỗi không rỗng/NFC. gold_chunk_ids là list chuỗi
không trùng, answered có ít nhất1, insufficient_context rỗng. Field bổ sung giữ nguyên.
Tool không kiểm chunk tồn tại/căn cứ pháp lý; dữ liệu do Team1/2 bàn giao đã kiểm chứng.

Dev/Test: chứa nguyên các object đầu vào,90/60, ID/câu hỏi không trùng giữa hai tập,
hợp đúng nguồn. Không đổi author, không bổ sung danh tính. Semantic review ngoài tool.

SplitReport: format_version, status=split_only, input basename/hash/count, seed,
stratify_by, counts/status_counts, output basename/hash/count, warnings. Không có
chữ ký/freeze approval hoặc trạng thái legally_approved. Hash tính bytesUTF-8 thực.
