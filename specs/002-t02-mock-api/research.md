# Research — T02
**Ngày:** 2026-10-09. Nguồn local code/Team3/T01; không nghiên cứu/thay công nghệ.
- Decision: cấu hình instance độc lập query/article. Rationale: không đổi request và không
  dùng question/header điều khiển. Alternatives: magic question và endpoint mới bị loại.
- Decision: nested query env fallback tới legacy; article default success. Rationale:
  giữ behavior cũ và phân biệt absent/blank; mọi enum sai fail. Không default rỗng.
- Decision: guard typed DTO trước complete/return. Rationale: hiện output null/invalid có
  thể thành 200/500. Mapping Team3 yêu cầu 502. Không sửa handler; không guard ngoài try.
- Decision: giữ tuple mock hiện có, không sinh luật/GT hoặc đòi AI/history thật.
- Read-only research agent t02_plan_review xác nhận các vị trí guard, boundary Unicode,
  first occurrence marker, C0/C11/C01, array order không phải contract, và precedence 400/404
  trước article mode. Không agent mutation/build/test.
- Chưa có unknown design; vận hành mới do Codex theo ủy quyền, cần Tuấn review sau.
