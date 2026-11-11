# Kế Hoạch Triển Khai Kỹ Thuật — Tuần 10
## Phân Hệ: Data & Retrieval (Team 1)

---

## 1. Thông Tin Chung & Mục Tiêu Trọng Tâm
- **Giai đoạn:** Tuần 10 (Sprint 7, hạn 16/11/2026), nghiệm thu dữ liệu cho Team 2 và Article Store cho Viewer.
- **Mục tiêu trọng tâm:**
  - Xử lý các điểm Team 2 báo trên `develop` `f4ceda3`: Golden lệch nguồn, Dev Set chưa đóng băng, thiếu câu ngoài phạm vi, registry thiếu `effective_date`.
  - VLRA-71/72: Article Store nguyên văn Điều và kiểm luồng mở Điều từ citation.

---

## 2. Bảng Phân Rã Công Việc (Task Breakdown)

| Mã Task | Người phụ trách | Tên công việc & Nội dung | Tiêu chí hoàn thành (DoD) |
| :--- | :--- | :--- | :--- |
| **T1-W10-1** | Team 1 | **Thống nhất Golden với nguồn Team 2** (gold_016, gold_021–025). | `test_imported_cases_unchanged_from_team2_source` 0 fail. |
| **T1-W10-2** | Team 1 | **Đóng băng Dev Set 110 câu** (VLRA-T2-29 của Team 2): `split`, `relevant_unit_groups`, hash. | Qua `scripts/eval_reranker.py::validate_dataset` không cần `--exploratory`; test khóa hash. |
| **T1-W10-3** | Team 1 | **≥ 30 câu ngoài phạm vi** cho cổng từ chối VLRA-T2-20. | `insufficient_context`, `gold_chunk_ids = []`, `citation` rỗng; có test. |
| **T1-W10-4** | Team 1 | **Bổ sung `effective_date`** cho 4 văn bản corpus mở rộng (+ xem VBHN 67). | Chỉ điền ngày xác minh được, ghi nguồn. |
| **VLRA-71** | Team 1 (+ Team 2/3) | **Tối ưu Article Store, nghiệm thu NFR-09 luồng Viewer.** | Article Store nguyên văn; `get_article` p95 ≤ 200 ms; NFR-09 E2E (Java → AI ≤ 10 s, FE ≤ 15 s) đo cùng Team 2/3. |
| **VLRA-72** | Team 1 (+ Team 3 UI) | **Kiểm tra hiển thị nguyên văn Điều, mở từ citation.** | Mọi citation P0 mở đúng Điều; chú thích sửa đổi, bảng biểu giữ nguyên. |

---

## 3. Ý Tưởng Giải Thuật & Thiết Kế Kỹ Thuật Chi Tiết

### 3.1. `relevant_unit_groups`
Theo `docs/team2_rag/reranker-evaluation.md` và `scripts/eval_reranker.py`: một nhóm gồm các subchunk tương đương của cùng một đơn vị pháp lý, không gộp các Khoản khác nhau. Trong `data/doanh-nghiep/processed/chunks.jsonl`, không gold chunk nào có subchunk cùng tiền tố `{document_id}__{article_id}__k{n}`, nên mỗi gold chunk là một nhóm: `[[id] for id in gold_chunk_ids]`.

### 3.2. Hash Dev Set
`sha256(NFC(json.dumps(cases, ensure_ascii=False, sort_keys=True, separators=(",", ":"))).encode("utf-8"))`, ghi ở `team1_data/golden/golden_phase1.manifest.json`. Hash không phụ thuộc định dạng xuống dòng/thụt lề của file.

### 3.3. Article Store
`data/doanh-nghiep/chunk_documents.py` xuất thêm `processed/articles.jsonl` (6 trường của `contracts/v0.1/internal_article.schema.json`). `content` = dòng `Điều N. Tên điều` + nguyên văn các khoản (giữ marker `[n]`), cuối Điều nối định nghĩa chú thích hợp nhất `[n] …`. `team2_rag/articles.py` đã ưu tiên đọc file này (không sửa code Team 2); trước đây Viewer dựng Điều bằng cách nối chunk nên lặp câu dẫn ở 48 Điều, mất tên Điều và mất chú thích sửa đổi ở 46 Điều.

---

## 4. Đặc Tả Hợp Đồng & Mock Data

| File | Người dùng | Ghi chú |
| :--- | :--- | :--- |
| `team1_data/golden/golden_phase1.json` | Team 2 (Dev Set) | 110 câu, `split: "dev"`, `relevant_unit_groups` |
| `team1_data/golden/golden_phase1.manifest.json` | Team 2 | `case_count`, `sha256`, quy tắc nhóm |
| `team1_data/golden/out_of_scope_v1.json` | Team 2 (VLRA-T2-20) | 33 câu `oos_001`–`oos_033`, cùng schema Golden + `reason`, `split: "dev"`, `relevant_unit_groups: []` |
| `data/doanh-nghiep/processed/articles.jsonl` | Team 2 API, Team 3 Viewer | 635 Điều, khóa `(document_id, article_id)` |

Chạy riêng câu ngoài phạm vi: `python -m scripts.eval_reranker --golden team1_data/golden/out_of_scope_v1.json …` (file riêng để không đổi số câu, trường bắt buộc và hash của Dev Set answered).

---

## 5. Blockers & Risks

| Rủi ro | Ảnh hưởng | Phương án |
| :--- | :--- | :--- |
| 70 câu `draft_needs_legal_review` và 33 câu ngoài phạm vi chưa có người soát pháp lý | Dev Set đóng băng để đo, chưa phải tập đã duyệt chuyên môn | Người có chuyên môn rà; sửa câu nào thì cập nhật hash và báo Team 2 |
| ID `gold_041`–`gold_044` trong `team2_rag/data/golden/golden_phase1_30cai.json` (Team 3 đóng góp) trùng ID với câu Team 1 khác nội dung | Gộp hai bộ theo ID sẽ lẫn câu; `test_sample_ids_do_not_collide_with_full_golden` của Team 2 đang fail (có từ trước) | Team 2 chọn đặt lại ID; Team 1 không sửa file Team 2 |
| vbpl.vn trả 403 cho truy cập tự động | Không lấy được ngày đăng Công báo của TT 31/2004/TT-BTC | Tra tay trên vbpl.vn/Công báo rồi điền |
| NFR-09 cần chạy Java + AI + FE thật | VLRA-71 chưa nghiệm thu E2E | Đo cùng Team 2/3 |

---

## 6. Kết Quả Thực Hiện (10/11/2026)

Nhánh `feature/team1-data/week-10-team2-acceptance` (T1-W10-1..4) và `feature/team1-data/week-10-article-store` (VLRA-71/72), đều từ `upstream/develop` `f4ceda3`.

| Mã Task | Trạng thái | Kết quả |
| :--- | :--- | :--- |
| T1-W10-1 | Xong | Bản Team 1 (31/10) là sao chép đúng; Team 2 sửa gold_016, gold_021 (câu hỏi/đáp án/gold) và đổi `author` gold_021–025 trong #49 (`fd52f6f`, 03/11). Đã nhập lại nguyên bản Team 2, không sửa file Team 2. gold_016 mới dùng `vbhn-67-vbhn-vpqh-v1__dieu-74__k1__0` (có trong corpus). |
| T1-W10-2 | Xong | 110 câu `split: "dev"`, mỗi gold chunk một nhóm; sha256 `92233687ad17bff6acf54c093a23c964619f2fca1899931949a8e5aa70efb918`. Test `test_dev_set_is_frozen`. 70 câu vẫn `draft_needs_legal_review`. |
| T1-W10-3 | Xong (chờ soát) | 33 câu: 20 lĩnh vực ngoài corpus (hình sự, hôn nhân gia đình, đất đai, thuế TNCN, giao thông, nghĩa vụ quân sự, hộ tịch, khám chữa bệnh, xuất nhập cảnh), 7 thiếu dữ kiện, 6 câu bẫy. Không kèm đáp án pháp lý. Test `tests/test_out_of_scope_v1.py`. |
| T1-W10-4 | Xong 3/4 | `nq-45-2017-qh14-v1` = 2017-06-21 (Điều 3 + ngày thông qua), `nd-359-2025-nd-cp-v1` = 2026-01-01 (khoản 1 Điều 2), `tt-07-tc-cdkt-v1` = 1964-02-21 (Điều 58 Chế độ + ngày Thông tư); nguồn ghi trong `note`. `tt-31-2004-tt-btc-v1` để trống: hiệu lực "sau 15 ngày kể từ ngày đăng Công báo", chưa có ngày đăng → `test_registry_metadata` còn fail đúng 1 văn bản. `vbhn-67-vbhn-vpqh-v1` giữ `null` (VBHN không có ngày hiệu lực riêng, như tuần 9). Chunk mở rộng vẫn mang ngày dự phòng = `issued_date`, chưa build lại. |
| VLRA-71 | Một phần | Article Store 635 Điều (1,5 MB); `get_article` nạp nguội 10,7 ms, p95 1,2 µs (635 Điều × 5). Chưa đo NFR-09 E2E (Team 2/3). Lỗi nguồn dữ liệu (ID sai, văn bản/Điều không có) đã có test 400/404 ở `team2_rag/tests/test_article_api.py`. |
| VLRA-72 | Xong phần Team 1 | `tests/test_article_store.py`: 2.576/2.576 chunk mở đúng Điều, mọi dòng chunk có trong nguyên văn, 46 Điều có chú thích sửa đổi đủ marker và định nghĩa. Corpus P0 không có bảng biểu trong phần Điều (phụ lục bị cắt khi tiền xử lý). Chạy `locateCitedUnit` của FE (không sửa) trên Article Store: tô sáng đúng 2.530/2.535 citation cấp Khoản; 5 ca hiện thông báo "đối chiếu toàn bộ Điều": 4 khoản có chữ (`Khoản 5a`, `1a`, `4a`) do regex FE chỉ nhận số, 1 ca `luat-76-2025-qh15-v1` Điều 1 khoản 5 trùng số với khoản được trích trong luật sửa đổi. |

**Kiểm thử** (`python3 -m pytest -q -p no:cacheprovider -rf`): baseline `f4ceda3` 20 failed / 614 passed; nhánh acceptance 14 failed / 617 passed; nhánh article-store 20 failed / 618 passed (6 lỗi Golden còn lại vì nhánh tách từ develop). Không fail/skip mới. `tests/test_golden_phase1.py` 0 fail; `tests/test_edge_cases_v1.py` còn 1 fail (TT 31/2004). 13 fail còn lại thuộc Team 2/3, có từ baseline.
