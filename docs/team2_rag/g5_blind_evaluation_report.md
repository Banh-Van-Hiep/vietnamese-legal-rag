# Báo Cáo Đánh Giá Định Tính (Chấm Mù Rubric 5 Tiêu Chí) — Mốc G5 (VLRA-79)
## Phân Hệ: RAG & LLM (Team 2 — Tuần 11)

- **Ticket Jira:** `VLRA-79` (`VLRA-T2-41`, `VLRA-T2-42`, `VLRA-T2-44`)
- **Dataset gốc:** `team1_data/golden/test_set_v1.json` (77 câu, SHA-256 `2d4b1f4db19e0c798518b4145f2a3f41d31676d2ddd1d1350fb69bd0b06de0a5`)
- **Mẫu chấm mù:** **40 câu hỏi phức tạp** (gồm toàn bộ 15 câu `multi_clause` nhiều điều kiện/tổng hợp nhiều điều luật và 25 câu `single_clause` trọng tâm), ẩn danh thành `Hệ thống A` và `Hệ thống B` với seed cố định (`20261124`).
- **Tệp dữ liệu liên quan:**
  - Gói câu hỏi ẩn danh: `docs/team2_rag/g5_blind_eval_package.json`
  - Khóa giải mã A/B: `docs/team2_rag/g5_blind_eval_key.json`
  - Phiếu điểm Giám khảo 1: `docs/team2_rag/g5_blind_scores_judge1.csv`
  - Phiếu điểm Giám khảo 2: `docs/team2_rag/g5_blind_scores_judge2.csv`

---

## 1. Bảng Tổng Hợp Điểm Chấm Mù 5 Tiêu Chí (`Baseline B0` vs `Target T0`)

Mỗi tiêu chí chấm trên thang `0–2` điểm (`0`: không đạt, `1`: đạt một phần, `2`: đạt hoàn toàn), tổng điểm tối đa **10 điểm/câu** (`n = 40` câu):

| Tiêu chí (Thang 0–2) | Giám khảo 1 (`B0` / `T0`) | Giám khảo 2 (`B0` / `T0`) | Trung bình 2 GK — **B0 (`BM25-only`)** | Trung bình 2 GK — **T0 (`Hybrid + BGE Rerank`)** | Chênh lệch (`T0 - B0`) |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **1. Đúng pháp lý (`legal`)** | `1,73` / `1,83` | `1,73` / `1,83` | `1,73` | **`1,83`** | **`+0,10`** |
| **2. Đầy đủ (`complete`)** | `1,73` / `1,83` | `1,73` / `1,83` | `1,73` | **`1,83`** | **`+0,10`** |
| **3. Căn cứ trích dẫn (`citation`)** | `1,75` / `1,83` | `1,75` / `1,68` | `1,75` | `1,75` | `0,00` |
| **4. Mạch lạc, dễ hiểu (`clarity`)** | `1,95` / `1,95` | `1,95` / `1,95` | `1,95` | `1,95` | `0,00` |
| **5. An toàn, không bịa (`safety`)** | `1,65` / `1,70` | `1,65` / `1,65` | `1,65` | **`1,68`** | **`+0,03`** |
| **Tổng điểm trung bình (Thang 10)** | `8,80` / `9,13` | `8,80` / `8,95` | **`8,80 / 10`** | **`9,04 / 10`** | **`+0,24`** |

- **Ghi chú về ca lỗi dịch vụ (`test_009`):** Ở câu `test_009`, `T0` gặp lỗi `LLMTimeoutError` nên nhận `0/10` điểm theo quy tắc chấm mù. Nếu xét riêng trên **39/40 câu hoàn thành phản hồi**, `T0` đạt trung bình **`9,27 / 10`** so với **`8,77 / 10`** của `B0` (`+0,50` điểm).
- **Đối chiếu ngưỡng NFR-03 (`T0 ≥ B0`):** **ĐẠT** (`9,04 ≥ 8,80`). `T0` vượt trội rõ rệt ở các câu hỏi tổng hợp nhiều điều khoản (`multi_clause`), tiêu biểu như `test_048` (`8,5` vs `5,0`), `test_049` (`10,0` vs `4,0`), `test_062` (`10,0` vs `1,0`) và `test_020` (`10,0` vs `2,0`).

---

## 2. Độ Đồng Thuận Giữa 2 Giám Khảo (Inter-Rater Agreement)

Đánh giá trên toàn bộ **80 cặp hệ thống–câu hỏi** (`40` câu × `2` hệ thống):

| Chỉ số đồng thuận | Giá trị đo được | Ngưỡng quy định (`tasks.md` mục 3.3) | Đánh giá |
| :--- | :---: | :---: | :---: |
| **Chênh lệch tuyệt đối trung bình (MAD)** | **`0,088` điểm** | Càng nhỏ càng tốt | Rất thấp |
| **Tỷ lệ cặp câu chênh `≤ 2` điểm** | **`100,00%`** (`80/80`) | Mức đồng thuận cao | Đạt tuyệt đối |
| **Hệ số tương quan thứ hạng Spearman ($\rho$)** | **`0,9994`** | Đồng thuận cao | Gần như đồng nhất |
| **Số cặp câu chênh `> 3` điểm cần rà soát lại** | **`0` câu** | Rà soát & ghi lý do nếu `> 3` điểm | Không phát sinh |

Các điểm chênh lệch nhỏ (`1–2` điểm ở 6/80 cặp: `test_048`, `test_053`, `test_055`, `test_057`, `test_012` trên một hệ thống) chủ yếu đến từ mức độ trừ điểm khắt khe hơn của Giám khảo 2 đối với các câu trả lời đúng ý chính nhưng viện dẫn thêm điều luật phụ ngoài phạm vi câu hỏi.
