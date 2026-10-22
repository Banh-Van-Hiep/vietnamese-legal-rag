package com.legalai.backend.conversation.persistence;

import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.sql.Timestamp;
import java.time.Instant;
import java.util.ArrayList;
import java.util.Collections;
import java.util.HexFormat;
import java.util.List;
import java.util.Objects;
import java.util.UUID;
import com.legalai.backend.ai.AiResponseValidator;
import com.legalai.backend.ai.dto.HistoryMessage;
import com.legalai.backend.ai.dto.RagAnswer;
import com.legalai.backend.chat.stream.StreamDtos.*;
import com.legalai.backend.common.exception.ApiError;
import com.legalai.backend.common.exception.ApiException;
import org.springframework.context.annotation.Profile;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.jdbc.support.GeneratedKeyHolder;
import org.springframework.stereotype.Repository;
import org.springframework.dao.DuplicateKeyException;
import org.springframework.transaction.PlatformTransactionManager;
import org.springframework.transaction.support.TransactionTemplate;
import org.springframework.boot.context.event.ApplicationReadyEvent;
import org.springframework.context.event.EventListener;
import tools.jackson.databind.json.JsonMapper;

/** Database-owned turn state. Every network call happens outside these short transactions. */
@Repository
@Profile("rag")
public class ChatStore {
    private final JdbcTemplate jdbc;
    private final TransactionTemplate tx;
    private final JsonMapper json = JsonMapper.builder().build();
    public record Turn(Meta meta, String question, List<HistoryMessage> history, Complete replay) { }
    private record Receipt(UUID id, Long conversation, Long user, Long assistant, String fingerprint,
            String state, String response, String error, Integer status, Instant created) { }

    public ChatStore(JdbcTemplate jdbc, PlatformTransactionManager manager) {
        this.jdbc = jdbc;
        this.tx = new TransactionTemplate(manager);
        this.tx.setTimeout(5);
    }
    public Turn accept(Request input) {
        recover();
        try { return tx.execute(s -> acceptInTransaction(input)); }
        catch (DuplicateKeyException race) {
            // First transaction rolled back, including its new conversation/messages.
            // Concurrent unique UUID winner is now visible; replay or pending, never another AI call.
            return tx.execute(s -> acceptInTransaction(input));
        }
    }
    private Turn acceptInTransaction(Request input) {
        Receipt old = receipt(input.clientRequestId());
        if (old != null) {
            if ("deleted".equals(old.state())) { throw error(404, "REQUEST_NOT_FOUND", false); }
            // Replay and delete must serialize on the same row, just like new query/delete.
            if (!lockIfPresent(old.conversation())) { throw error(404, "REQUEST_NOT_FOUND", false); }
            old = receipt(input.clientRequestId());
            if (old == null || "deleted".equals(old.state())) { throw error(404, "REQUEST_NOT_FOUND", false); }
            if (!Objects.equals(old.fingerprint(), hash(input.question())) ||
                    input.conversationId() != null && !input.conversationId().equals(old.conversation())) {
                throw error(409, "REQUEST_ID_CONFLICT", false).inNumericConversation(old.conversation());
            }
            if ("pending".equals(old.state())) {
                throw error(409, "REQUEST_IN_PROGRESS", true).inNumericConversation(old.conversation());
            }
            if ("failed".equals(old.state())) { throw failure(old); }
            Complete response = json.readValue(old.response(), Complete.class);
            return new Turn(meta(old), input.question(), List.of(), response);
        }
        Instant now = Instant.now().truncatedTo(java.time.temporal.ChronoUnit.MICROS);
        jdbc.update("INSERT INTO chat_receipts(client_request_id,fingerprint,state,created_at) VALUES(?,?,'pending',?)",
                input.clientRequestId(), hash(input.question()), Timestamp.from(now));
        long conversation = input.conversationId() == null ? createInTransaction("Hội thoại mới", now).id() : input.conversationId();
        lock(conversation);
        checkBusy(conversation);
        int sequence = jdbc.queryForObject("SELECT COALESCE(MAX(sequence_no),0)+1 FROM chat_messages WHERE conversation_id=?",
                Integer.class, conversation);
        long user = insert("INSERT INTO chat_messages(conversation_id,client_request_id,sequence_no,role,state,content,created_at)"
                + " VALUES(?,?,?,'user','completed',?,?)", conversation, input.clientRequestId(), sequence, input.question(), Timestamp.from(now));
        long assistant = insert("INSERT INTO chat_messages(conversation_id,client_request_id,sequence_no,role,state,created_at,pending_conversation_id)"
                + " VALUES(?,?,?,'assistant','pending',?,?)", conversation, input.clientRequestId(), sequence + 1, Timestamp.from(now), conversation);
        jdbc.update("UPDATE chat_receipts SET conversation_id=?,user_message_id=?,assistant_message_id=? WHERE client_request_id=?",
                conversation, user, assistant, input.clientRequestId());
        touch(conversation);
        return new Turn(new Meta(conversation, input.clientRequestId(), user, assistant, now), input.question(), history(conversation, sequence), null);
    }
    public Complete complete(Turn turn, RagAnswer result) {
        AiResponseValidator.query(result);
        return tx.execute(s -> {
            if (!lockIfPresent(turn.meta().conversationId())) { return null; }
            Receipt r = receipt(turn.meta().clientRequestId());
            if (r == null || !"pending".equals(r.state())) { return null; }
            Complete complete = Complete.from(turn.meta(), result);
            jdbc.update("UPDATE chat_messages SET state='completed',content=?,answer_status=?,pending_conversation_id=NULL WHERE id=? AND state='pending'",
                    result.answer(), result.status(), turn.meta().assistantMessageId());
            for (var c : result.citations()) {
                jdbc.update("INSERT INTO chat_citations(assistant_message_id,citation_id,chunk_id,document_id,article_id,document_title,article,clause,point,source_url) VALUES(?,?,?,?,?,?,?,?,?,?)",
                        turn.meta().assistantMessageId(), c.citation_id(), c.chunk_id(), c.document_id(), c.article_id(),
                        c.document_title(), c.article(), c.clause(), c.point(), c.source_url());
            }
            jdbc.update("UPDATE chat_receipts SET state='completed',response_snapshot=? WHERE client_request_id=? AND state='pending'",
                    json.writeValueAsString(complete), r.id());
            touch(r.conversation());
            return complete;
        });
    }
    public ApiException fail(Turn turn, ApiException error) {
        return tx.execute(s -> failInTransaction(turn.meta().clientRequestId(), turn.meta().conversationId(), error));
    }
    private ApiException failInTransaction(UUID id, long conversation, ApiException error) {
        if (!lockIfPresent(conversation)) { return null; }
        Receipt r = receipt(id);
        if (r == null || "completed".equals(r.state()) || "deleted".equals(r.state())) { return null; }
        if ("failed".equals(r.state())) { return failure(r); }
        jdbc.update("UPDATE chat_messages SET state='failed',content=NULL,answer_status=NULL,error_code=?,pending_conversation_id=NULL WHERE id=? AND state='pending'",
                error.body().error().code(), r.assistant());
        jdbc.update("UPDATE chat_receipts SET state='failed',error_snapshot=?,logical_status=? WHERE client_request_id=? AND state='pending'",
                json.writeValueAsString(error.body()), error.status(), id);
        touch(conversation);
        return error.inNumericConversation(conversation);
    }
    @EventListener(ApplicationReadyEvent.class)
    public void recover() {
        var stale = jdbc.query("SELECT * FROM chat_receipts WHERE state='pending' AND created_at<? ORDER BY conversation_id,client_request_id",
                this::receiptRow, Timestamp.from(Instant.now().minusSeconds(60)));
        for (Receipt r : stale) {
            if (r.conversation() != null) { tx.executeWithoutResult(s -> failInTransaction(r.id(), r.conversation(),
                    error(503, "PROCESSING_INTERRUPTED", true))); }
        }
    }
    public List<Conversation> conversations() {
        recover();
        return jdbc.query("SELECT * FROM chat_conversations ORDER BY updated_at DESC,id ASC", this::conversationRow);
    }
    public Conversation conversation(long id) {
        recover();
        var rows = jdbc.query("SELECT * FROM chat_conversations WHERE id=?", this::conversationRow, id);
        if (rows.isEmpty()) { throw error(404, "CONVERSATION_NOT_FOUND", false); }
        return rows.getFirst();
    }
    public Conversation create(String title) {
        return tx.execute(s -> createInTransaction(title, Instant.now().truncatedTo(java.time.temporal.ChronoUnit.MICROS)));
    }
    private Conversation createInTransaction(String title, Instant now) {
        return new Conversation(insert("INSERT INTO chat_conversations(title,created_at,updated_at) VALUES(?,?,?)",
                title, Timestamp.from(now), Timestamp.from(now)), title, now, now);
    }
    public List<Message> messages(long id) {
        recover();
        return tx.execute(s -> {
            lock(id);
            return jdbc.query("SELECT * FROM chat_messages WHERE conversation_id=? ORDER BY sequence_no", (r, n) ->
                    new Message(r.getLong("id"), id, r.getObject("client_request_id", UUID.class), r.getInt("sequence_no"),
                        r.getString("role"), r.getString("state"), r.getString("content"), r.getString("answer_status"),
                        citations(r.getLong("id")), r.getString("error_code"), r.getTimestamp("created_at").toInstant()), id);
        });
    }
    public void delete(long id) {
        recover();
        tx.executeWithoutResult(s -> {
            lock(id); checkBusy(id);
            jdbc.update("UPDATE chat_receipts SET state='deleted',fingerprint=NULL,response_snapshot=NULL,error_snapshot=NULL,logical_status=NULL,deleted_at=? WHERE conversation_id=?",
                    Timestamp.from(Instant.now()), id);
            jdbc.update("DELETE FROM chat_conversations WHERE id=?", id);
        });
    }
    private List<PublicCitation> citations(long assistant) {
        return jdbc.query("SELECT * FROM chat_citations WHERE assistant_message_id=? ORDER BY LENGTH(citation_id),citation_id", (r, n) ->
                new PublicCitation(r.getString("citation_id"), r.getString("chunk_id"), r.getString("document_id"),
                    r.getString("article_id"), r.getString("document_title"), r.getString("article"),
                    r.getString("clause"), r.getString("point"), r.getString("source_url")), assistant);
    }
    private List<HistoryMessage> history(long conversation, int before) {
        var pairs = jdbc.query("SELECT u.content AS question,a.content AS answer FROM chat_messages u JOIN chat_messages a"
                + " ON u.client_request_id=a.client_request_id AND u.conversation_id=a.conversation_id"
                + " WHERE u.conversation_id=? AND u.role='user' AND a.role='assistant' AND a.state='completed'"
                + " AND a.answer_status='answered' AND u.sequence_no<? ORDER BY u.sequence_no DESC LIMIT 5",
                (r, n) -> List.of(new HistoryMessage("user", r.getString("question")), new HistoryMessage("assistant", r.getString("answer"))),
                conversation, before);
        var selected = new ArrayList<List<HistoryMessage>>();
        int count = 0;
        for (var pair : pairs) {
            int size = pair.stream().mapToInt(m -> m.content().codePointCount(0, m.content().length())).sum();
            if (count + size > 20000) { break; }
            selected.add(pair); count += size;
        }
        Collections.reverse(selected);
        return selected.stream().flatMap(List::stream).toList();
    }
    private Receipt receipt(UUID id) {
        var rows = jdbc.query("SELECT * FROM chat_receipts WHERE client_request_id=?", this::receiptRow, id);
        return rows.isEmpty() ? null : rows.getFirst();
    }
    private Receipt receiptRow(ResultSet r, int n) throws SQLException {
        return new Receipt(r.getObject("client_request_id", UUID.class), r.getObject("conversation_id", Long.class),
                r.getObject("user_message_id", Long.class), r.getObject("assistant_message_id", Long.class),
                r.getString("fingerprint"), r.getString("state"), r.getString("response_snapshot"),
                r.getString("error_snapshot"), r.getObject("logical_status", Integer.class), r.getTimestamp("created_at").toInstant());
    }
    private Conversation conversationRow(ResultSet r, int n) throws SQLException {
        return new Conversation(r.getLong("id"), r.getString("title"), r.getTimestamp("created_at").toInstant(),
                r.getTimestamp("updated_at").toInstant());
    }
    private Meta meta(Receipt r) {
        return new Meta(r.conversation(), r.id(), r.user(), r.assistant(), r.created());
    }
    private ApiException failure(Receipt r) {
        ApiError e = json.readValue(r.error(), ApiError.class);
        return new ApiException(r.status(), e.error().code(), e.error().message(), e.error().retryable()).inNumericConversation(r.conversation());
    }
    private void lock(long id) {
        if (!lockIfPresent(id)) { throw error(404, "CONVERSATION_NOT_FOUND", false); }
    }
    private boolean lockIfPresent(long id) {
        return !jdbc.query("SELECT id FROM chat_conversations WHERE id=? FOR UPDATE", (r, n) -> r.getLong(1), id).isEmpty();
    }
    private void checkBusy(long id) {
        if (jdbc.queryForObject("SELECT COUNT(*) FROM chat_messages WHERE pending_conversation_id=?", Long.class, id) > 0) {
            throw error(409, "CONVERSATION_BUSY", true).inNumericConversation(id);
        }
    }
    private void touch(long id) { jdbc.update("UPDATE chat_conversations SET updated_at=? WHERE id=?", Timestamp.from(Instant.now()), id); }
    private long insert(String sql, Object... args) {
        var key = new GeneratedKeyHolder();
        jdbc.update(connection -> {
            var statement = connection.prepareStatement(sql, new String[] {"id"});
            for (int i = 0; i < args.length; i++) { statement.setObject(i + 1, args[i]); }
            return statement;
        }, key);
        return Objects.requireNonNull(key.getKey()).longValue();
    }
    private static String hash(String value) {
        try { return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(value.getBytes(StandardCharsets.UTF_8))); }
        catch (NoSuchAlgorithmException e) { throw new IllegalStateException(e); }
    }
    private static ApiException error(int status, String code, boolean retryable) {
        return new ApiException(status, code, switch (code) {
            case "CONVERSATION_NOT_FOUND" -> "Không tìm thấy hội thoại.";
            case "PROCESSING_INTERRUPTED" -> "Lượt xử lý đã bị gián đoạn. Hãy gửi một lượt mới.";
            case "REQUEST_NOT_FOUND" -> "Lượt hỏi thuộc hội thoại đã xóa.";
            case "REQUEST_ID_CONFLICT" -> "ID lượt hỏi đã được dùng cho yêu cầu khác.";
            default -> "Hội thoại hoặc lượt hỏi đang được xử lý.";
        }, retryable);
    }
}
