# Data model — chat v2.0

- Conversation: BIGINT identity id, title 1–100 code point, createdAt/updatedAt UTC.
- Message: BIGINT identity id (JS safe), conversationId FK cascade, clientRequestId UUID,
  sequenceNo ≥1 unique/conv, role user/assistant, state pending/completed/failed,
  content/answerStatus/errorCode nullable theo state, createdAt immutable.
  pendingConversationId unique và chỉ có khi assistant pending.
- Citation: assistantMessageId FK, citationId C1..C10, chín giá trị provenance giữ nguyên,
  unique message+label và message+chunk; không citation cho insufficient/failed.
- RequestReceipt: UUID PK, conversation binding, user/assistant IDs, hash question trimmed,
  pending/completed/failed, response/error snapshot, logical HTTP status, createdAt/deletedAt.
  Tombstone giữ IDs/time/deleted, loại hash và snapshots.
- Pending → completed/failed; không chuyển terminal ngược, late output bị bỏ.
- Public IDs integer 1..9007199254740991; clientRequestId UUIDv4; fields camelCase.
- History chỉ role/content, tối đa 5 cặp answered/completed và tổng ≤20000 code point.
