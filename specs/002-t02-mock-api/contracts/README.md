# T02 — Interface references
Nguồn [team3.md](../../../docs/team3_fullstack/team3.md); đây không shared contract mới.
POST /api/v1/query, GET /api/v1/documents/{document_id}/articles/{article_id}, health giữ nguyên.
Request/response/constraints tại [spec](../spec.md) và [data model](../data-model.md).
500 INTERNAL_ERROR false, 502 UPSTREAM_INVALID_RESPONSE false,
503 SERVICE_UNAVAILABLE true, 504 UPSTREAM_TIMEOUT true; envelope chỉ error.
X-Request-ID mọi lần gọi; query sau accept kể cả 502 phải X-Conversation-ID đúng lượt.
CORS/phương thức/body/unknown input kế thừa T01; không JSON403 hoặc đổi406.
Không public query parameter/field/header/route chọn scenario. Cấu hình nội bộ có hai key
mới theo [plan](../plan.md); legacy key và Q2 vẫn giữ. Schema Team2 lệch đã ghi trong spec,
không dùng thay API Team3 hoặc sửa schema trong T02.
