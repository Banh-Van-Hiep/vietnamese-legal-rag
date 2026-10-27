# Data model — FE integration

Public types đúng Docs §9: positive safe integer IDs, camelCase, UUIDv4 clientRequestId.
Meta5fields, Complete8fields, PublicCitation9fields, Message11fields; arrays cho lists.
UI model nội bộ vẫn string keys và metadata cũ qua adapter, không gửi model đó nguyên
trạng lên network. Legal document/article IDs vẫn versioned string ASCII.

Local turn: UUID, question trimmed1..2000 codepoints, optional bound conv, message keys,
state pending/answered/insufficient/failed/unknown. Unknown giữ UUID và question cho
reconcile/replay; terminal clear draft. Session storage phục hồi receipt tối thiểu khi
reload, không là nguồn history pháp lý. Known failed mới được tạo UUID mới khi retry.
Một pending conv chặn send mới. Stop/abort nhận stream không hứa hủy backend AI.

Complete IDs/time khớp meta/request; citations khớp marker và không duplicate chunk.
History lấy từ Backend, không tự gửi history/context/model/scenario từ FE.
