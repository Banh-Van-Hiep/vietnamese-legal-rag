# Nguồn mở rộng corpus

Danh mục văn bản cần lấy (`*.csv`) và báo cáo kết quả (`*_report.csv`) cho các đợt mở rộng
phạm vi pháp luật về doanh nghiệp theo Docs v2.0 §1.4.

## Định dạng danh mục

| Cột | Ý nghĩa |
| --- | --- |
| `so_ky_hieu` | Số ký hiệu đúng như trên vbpl.vn, ví dụ `17/2023/QH15`, `92/2024/NĐ-CP` |
| `muc` | `P0` hoặc `P1` |
| `nhom` | `thanh_lap_dang_ky`, `von_thanh_vien_co_dong`, `quan_tri_dai_dien`, `to_chuc_lai_cham_dut`, `dan_su_thuong_mai`, `dau_tu_dieu_kien_kinh_doanh`, `thue_ke_toan`, `lao_dong_bhxh`, `pha_san_che_tai` |
| `ghi_chu` | Tên ngắn để người review đọc |

## Chạy

Trên máy có Internet, từ thư mục gốc repo:

```powershell
python -m pip install pyarrow huggingface_hub
python scripts\fetch_hf_legal_docs.py --list data\doanh-nghiep\sources\pilot_30.csv
```

Script ghi `raw/{document_id}/` (source.txt, fetch_info.json, source.html bị Git bỏ qua),
`registry/hf_pending.json` và báo cáo. Sau khi review, gộp `hf_pending.json` vào
`registry/documents.json`, sinh `interim/` bằng `clean_text` của `scripts/preprocess_legal_data.py`,
chạy `python data/doanh-nghiep/chunk_documents.py` và `python scripts/validate_chunks.py`.
Không ghi đè `raw/{id}` đã có trừ khi dùng `--force`.
