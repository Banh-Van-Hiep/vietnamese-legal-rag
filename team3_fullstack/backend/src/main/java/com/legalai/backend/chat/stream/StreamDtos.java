package com.legalai.backend.chat.stream;

import java.time.Instant;
import java.util.List;
import java.util.UUID;
import com.legalai.backend.ai.dto.Citation;
import com.legalai.backend.ai.dto.RagAnswer;

/** Public v2.0 wire types; internal DTOs deliberately remain snake_case. */
public final class StreamDtos {
    private StreamDtos() { }
    public static final long MAX_ID = 9_007_199_254_740_991L;
    public record Request(String question, UUID clientRequestId, Long conversationId) { }
    public record Meta(long conversationId, UUID clientRequestId, long userMessageId,
            long assistantMessageId, Instant createdAt) { }
    public record PublicCitation(String citationId, String chunkId, String documentId, String articleId,
            String documentTitle, String article, String clause, String point, String sourceUrl) {
        public static PublicCitation from(Citation c) {
            return new PublicCitation(c.citation_id(), c.chunk_id(), c.document_id(), c.article_id(),
                    c.document_title(), c.article(), c.clause(), c.point(), c.source_url());
        }
    }
    public record Complete(long conversationId, UUID clientRequestId, long userMessageId,
            long assistantMessageId, String status, String answer, List<PublicCitation> citations, Instant createdAt) {
        public static Complete from(Meta meta, RagAnswer answer) {
            return new Complete(meta.conversationId(), meta.clientRequestId(), meta.userMessageId(),
                    meta.assistantMessageId(), answer.status(), answer.answer(),
                    answer.citations().stream().map(PublicCitation::from).toList(), meta.createdAt());
        }
    }
    public record Conversation(long id, String title, Instant createdAt, Instant updatedAt) { }
    public record Message(long id, long conversationId, UUID clientRequestId, int sequenceNo,
            String role, String state, String content, String answerStatus, List<PublicCitation> citations,
            String errorCode, Instant createdAt) { }
}
