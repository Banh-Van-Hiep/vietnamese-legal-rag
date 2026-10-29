# Validation — public contract tại v0.1

**Ngày kiểm chứng:**30/10/2026. **Kết quả:** đạt phạm vi contract public.

## Phạm vi kiểm chứng

Payload request và SSE, marker/citation/binding; hồi quy public/internal API và CLI.

## Expected / Actual

| Kiểm tra | Expected | Actual |
| --- | --- | --- |
| Public contract | Schema hợp lệ, positive nhận/negative từ chối | 76/76: 15 positive, 61 negative; exit0 |
| Wire HTTP mới | Request/meta/delta/complete hợp schema và binding | 4 payload, binding PASS |
| Java API regression | SSE và JSON legacy vẫn chạy theo test hiện có | StreamApiTests12/12 + MockApiTests16/16 =28/28, 0 fail/error/skip |
| Team2 regression | API thực với fake pipeline/mock còn hợp schema nội bộ | Nhóm API/mock/pipeline/reranker/Hybrid:48 test +81 subtest đạt, dùng dependency giả |
| CLI thất bại | Fixture lỗi/thiếu schema/thiếu wire không được PASS | Bản copy target: exit1/2/2 đúng |
| Resolver | Không truy cập mạng để resolve schema | Registry local cho request + stream, wire validation đạt |

## Bàn giao và điều kiện còn lại

- Contract76/76, payload thực và API regression đạt.
- ERD/wireframe đã được xác nhận.
- Phạm vi public contract đạt. Bộ test mở rộng Team2 còn1 lỗi Golden gold_041; theo dõi tại nghiệm thu tuần5.

Bằng chứng: `backend/target/final-acceptance-20261030/`.

[Spec](spec.md) · [Tasks](tasks.md) · [Nghiệm thu tuần4](../verification.md).
