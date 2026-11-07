# Kế Hoạch Triển Khai Kỹ Thuật — Tuần 9
## Phân Hệ: Data & Retrieval (Team 1)

---

## 1. Thông Tin Chung & Mục Tiêu Trọng Tâm
- **Giai đoạn:** Tuần 9 (phối hợp Team 2 kiểm chứng citation).
- **Mục tiêu trọng tâm:**
  - Phân loại lỗi citation (sai Điều/Khoản, sai phiên bản sửa đổi) để Team 1 và Team 2 dùng chung một bảng mã lỗi.
  - Kiểm tra URL nguồn và hiệu lực của 8 văn bản trong `data/doanh-nghiep/registry/documents.json`.
  - Đối chiếu citation của lượt eval gần nhất của Team 2 theo bảng mã lỗi.

---

## 2. Bảng Phân Rã Công Việc (Task Breakdown)

| Mã Task | Người phụ trách | Tên công việc & Nội dung | Tiêu chí hoàn thành (DoD) |
| :--- | :--- | :--- | :--- |
| **VLRA-64** | Thành viên A | **Phân tích lỗi citation & kiểm tra URL nguồn/hiệu lực**<br>- Bảng loại lỗi: sai Điều · sai Khoản/Điểm · sai phiên bản sửa đổi · URL sai/chết · văn bản hết hiệu lực.<br>- Rà 8 văn bản registry: `source_url` mở được, khớp số hiệu, `legal_status`/`effective_date` đúng vbpl.vn.<br>- Đối chiếu citation lượt eval gần nhất của Team 2. | - Bảng mã lỗi E1–E5 (mục 4.1) bàn giao cho VLRA-65.<br>- Kết quả rà 8 văn bản và đối chiếu citation ghi ở mục 6.<br>- Mục chưa kiểm được ghi rõ lý do. |
| **VLRA-65** | Thành viên B | Dùng bảng mã lỗi của VLRA-64 (theo mô tả Jira). | Theo Jira VLRA-65. |

---

## 3. Ý Tưởng Giải Thuật & Thiết Kế Kỹ Thuật Chi Tiết

### 3.1. Nguồn dữ liệu kiểm tra

| Nguồn | Ghi chú |
| :--- | :--- |
| `data/doanh-nghiep/registry/documents.json` | 8 văn bản |
| `data/doanh-nghiep/processed/chunks.jsonl` | 2.576 chunk, sha256 `042bd7f1…5466`, trùng hash corpus của lượt eval Team 2 |
| `data/doanh-nghiep/interim/vbhn-67-vbhn-vpqh-v1.txt` | Chú thích `[n]` của VBHN 67 cho biết điều/khoản nào bị Luật 03/2022 hoặc 76/2025 sửa |
| `team2_rag/data/evaluation/colab-20261102/` | Lượt eval gần nhất của Team 2 (02/11/2026), 110 câu, nhánh BGE truncate; **không gọi LLM** |
| `team2_rag/data/golden/golden_sample_5qa.json` | Bộ 5 câu của `test_answer_citation_accuracy.py` |

### 3.2. Cách đối chiếu
- **Nhãn Golden và gold chunk:** tách nhãn `citation` thành các bộ (văn bản, Điều, Khoản, Điểm), rồi so với `document_id`/`article`/`clause` của `gold_chunk_ids`.
- **Phiên bản sửa đổi:** một chunk Luật 59/2020 tính là đã bị sửa nếu điều/khoản tương ứng trong VBHN 67 có chú thích `[n]`. 906 chunk Luật 59/2020 có 861 chunk giống hệt VBHN 67 (bỏ qua khoảng trắng và chú thích), 45 chunk khác.
- **Rủi ro trong context:** lượt 02/11 không có câu trả lời LLM, nên chỉ xét top-5 context (`context_cutoff = 5`) mà LLM sẽ nhận, trước và sau rerank.
- **Registry:** kiểm HTTP `source_url`. Khi bị chặn, đối chiếu offline số hiệu/ngày với phần đầu và điều khoản hiệu lực của văn bản trong `interim/`.

---

## 4. Đặc Tả Hợp Đồng & Mock Data

### 4.1. Bảng mã lỗi citation (bàn giao VLRA-65)

| Mã | Loại lỗi | Định nghĩa | Cách phát hiện |
| :--- | :--- | :--- | :--- |
| E1 | Sai Điều | Điều được trích không chứa căn cứ; hoặc gold/context không có Điều đúng | So `(document_id, article)` với gold |
| E2 | Sai Khoản/Điểm | Đúng Điều nhưng khoản/điểm thiếu hoặc thừa so với gold | So `clause`/`point` khi đã khớp Điều |
| E3 | Sai phiên bản sửa đổi | Trích Luật 59/2020 gốc cho điều/khoản đã bị sửa, bổ sung, bãi bỏ; hoặc gold và citation khác văn bản trong khi nội dung khác nhau | Chú thích `[n]` tại điều/khoản trong VBHN 67 |
| E4 | URL sai/chết | `source_url` không mở được, không trỏ đúng văn bản/số hiệu, hoặc không phải nguồn chính thức | HTTP check, so số hiệu trên trang |
| E5 | Văn bản hết hiệu lực | Văn bản/điều đã hết hiệu lực tại ngày hỏi, hoặc `legal_status`/`effective_date` sai so với nguồn chính thức | So vbpl.vn / Công báo |
| (phụ) | Nhãn thiếu tên văn bản | Nhãn chỉ có "Điều N - <tên điều>" | Không xác định được văn bản |

Quy ước: Luật 59/2020 và VBHN 67 có nội dung giống hệt nhau thì **không tính E3**.

### 4.2. Mẫu ghi nhận lỗi

| Câu | Nhãn citation | Mã lỗi | Bằng chứng |
| :--- | :--- | :--- | :--- |
| gold_014 | Khoản 2 Điều 24 - Điều lệ công ty | E2, (phụ) | Gold gồm khoản 1–4 Điều 24 Luật 59/2020 |
| gold_011 | Điều 16 - Các hành vi bị nghiêm cấm | E3, (phụ) | Gold là bản 59/2020; khoản 1, 4, 5 đã bị Luật 76/2025 sửa (chú thích [9]–[11] VBHN 67) |

---

## 5. Blockers & Risks

| Rủi ro | Ảnh hưởng | Phương án |
| :--- | :--- | :--- |
| vbpl.vn chặn bot (403, `Ws-Action: bot`); congbao.chinhphu.vn, xaydungchinhsach.chinhphu.vn, thuvienphapluat.vn bị proxy môi trường chặn | Chưa kiểm trực tuyến được URL và hiệu lực, nên **VLRA-64 chưa Done** | Chạy lại phần kiểm trực tuyến từ máy truy cập được, hoặc mở các host này trong môi trường |
| Lượt eval 02/11 không gọi LLM | Chưa đo được lỗi citation trong câu trả lời thật | Đối chiếu lại bằng bảng mã lỗi khi Team 2 có lượt chạy có LLM |
| Chunk VBHN 67 thiếu Điều 11 (Luật 03/2022) và Điều 3 (Luật 76/2025) về chuyển tiếp | Câu hỏi về chuyển tiếp dễ bị trích sai phiên bản (E3) | Team 1 xem lại quy tắc chunking cho VBHN |

---

## 6. Kết Quả Thực Hiện (07/11/2026)

### 6.1. Rà 8 văn bản registry (offline)

| Văn bản | Số hiệu & ngày ban hành | effective_date | legal_status | URL | Phát hiện |
| :--- | :--- | :--- | :--- | :--- | :--- |
| 59/2020/QH14 | Khớp | 2021-01-01: khớp đầu VBHN 67 | het_hieu_luc_mot_phan: hợp lý (đã bị 03/2022, 76/2025 sửa) | vbpl.vn | — |
| 76/2025/QH15 | Khớp | 2025-07-01: khớp Điều 3 | con_hieu_luc | Công báo | — |
| 67/VBHN-VPQH | Khớp | null (VBHN không có ngày hiệu lực riêng) | con_hieu_luc | Công báo | Lưu ý L1, L2 |
| 7566/VBHN-BKHĐT | Khớp | 2021-04-01: ngày hiệu lực NĐ 47/2021 | **chưa kiểm** | Slug `nghi-dinh-so-47-2021-nd-cp-33620/35577` | **Nghi E4**: URL có vẻ trỏ trang NĐ 47/2021, không phải VBHN 7566 |
| 168/2025/NĐ-CP | Khớp | 2025-07-01: khớp | con_hieu_luc | Cổng TTĐT Chính phủ | Nên dùng URL vbpl/Công báo |
| 122/2021/NĐ-CP | Khớp | 2022-01-01: **chưa kiểm** (bản trích không có điều hiệu lực) | het_hieu_luc_mot_phan: hợp lý theo NĐ 288/2026 | Công báo | — |
| 288/2026/NĐ-CP | Khớp | 2026-07-21: khớp ("kể từ ngày ký") | con_hieu_luc | thuvienphapluat.vn | **Nghi E4**: không phải nguồn chính thức |
| 68/2025/TT-BTC | Khớp | 2025-07-01: khớp | **chưa kiểm** (TT 121/2026 chưa có trong corpus) | vbpl.vn | — |

- **L1.** Registry để `effective_date = null` cho VBHN 67, nhưng chunk ghi `2025-08-15`, vì `chunk_documents.py:220` lấy `issued_date` khi trường này rỗng. Lệch này làm 65/110 câu Golden khác metadata registry. Không được hiển thị giá trị này là "ngày hiệu lực".
- **L2.** Registry VBHN 67 ghi `article_count = 220`, `last_article = "3"` vì tính cả hai điều chuyển tiếp ở cuối văn bản. Chunk chỉ đến Điều 218, nên hai điều này không có trong index.

### 6.2. Nhãn Golden và gold chunk (110 câu + 5 câu mẫu)

| Loại | Số câu | Câu |
| :--- | :--- | :--- |
| E1 Sai Điều | 0 | — |
| E2 Sai Khoản/Điểm | 1 | gold_014 |
| E3 Sai phiên bản | 3 | gold_011 (Điều 16: khoản 1, 4, 5 đã sửa), gold_012 (Điều 20: khoản 3 đã sửa), gold_013 (Điều 23: thiếu khoản 10 do 76/2025 bổ sung) |
| (phụ) Nhãn thiếu tên văn bản | 5 | gold_011 đến gold_015 |
| Chunk gold không tồn tại / `gold_citations` lệch metadata | 0 | — |

Cả 4 câu lỗi E2/E3 đều thuộc nhóm `team2_reviewed`.

### 6.3. Rủi ro trong top-5 context (BGE truncate, 110/110 câu)

| Chỉ số | Hybrid top-5 | Sau rerank top-5 |
| :--- | :--- | :--- |
| Đủ gold trong context | 88 | 85 |
| Thiếu gold, có cùng khoản nhưng khác phiên bản (rủi ro E3) | 1 | 4 (gold_005, 011, 053, 054) |
| Thiếu gold, có cùng Điều nhưng khác khoản (rủi ro E2) | 11 | 11 |
| Thiếu gold, không có Điều đúng (rủi ro E1) | 12 | 15 |
| Context có chunk Luật 59/2020 đã bị sửa (rủi ro E3 thật) | 6 | 7 (gold_011, 026, 031, 039, 054, 082, 088) |
| Context chứa cả hai phiên bản của cùng một khoản | 81 | 83 |

- Ở gold_005, 053 và 054, hai phiên bản có nội dung giống nhau. Câu bị tính thiếu gold chỉ vì Golden chấp nhận đúng một `chunk_id`. Riêng gold_011, gold là bản cũ, nên câu trả lời đúng sẽ bị chấm sai.

### 6.4. Chưa kiểm được
1. Kiểm trực tuyến `source_url` và `legal_status`/`effective_date` theo vbpl.vn cho cả 8 văn bản (bị chặn như mục 5).
2. Hiệu lực của 7566/VBHN-BKHĐT và 68/2025/TT-BTC, ngày hiệu lực của 122/2021/NĐ-CP: corpus không đủ căn cứ.
3. Lỗi citation trong câu trả lời LLM thật.

### 6.5. Đề xuất
- **Team 1:** bổ sung `amended_by`/`amendment_notes` cho chunk Luật 59/2020 từ chú thích VBHN 67 (hiện 2.576/2.576 chunk để rỗng); xem lại L2; thay URL không chính thức của 168/2025 và 288/2026; xác nhận URL 7566.
- **Chuyển Team 2** (chỉ ghi nhận, Team 1 không sửa): xem lại gold của gold_011–014; cho group gold nhận chunk tương đương giữa 59/2020 và VBHN 67 khi nội dung trùng; cân nhắc khử trùng hai phiên bản trong context, ưu tiên VBHN.
