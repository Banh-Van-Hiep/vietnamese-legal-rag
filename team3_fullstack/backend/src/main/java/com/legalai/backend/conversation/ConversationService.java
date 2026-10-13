package com.legalai.backend.conversation;

import java.time.Instant;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.UUID;
import com.legalai.backend.ai.dto.RagAnswer;
import com.legalai.backend.chat.dto.ChatRequest;
import com.legalai.backend.chat.dto.ChatResponse;
import com.legalai.backend.common.exception.ApiException;
import com.legalai.backend.common.web.PageResponse;
import com.legalai.backend.common.web.PageResponse.PageRequest;
import org.springframework.context.annotation.Profile;
import org.springframework.stereotype.Service;

/** In-memory mock store. State and request deduplication disappear on restart. */
@Service
@Profile("mock")
public class ConversationService {
    private final Map<UUID, Conversation> conversations = new HashMap<>();
    private final Map<UUID, List<Message>> messages = new HashMap<>();
    private final Map<UUID, Turn> requests = new HashMap<>();
    private final Set<UUID> deletedRequests = new HashSet<>();

    public static final class Turn {
        private final UUID requestId;
        private final String question;
        private final UUID conversationId;
        private final Message user;
        private final Message assistant;
        private ChatResponse response;
        private ApiException failure;

        private Turn(ChatRequest request, UUID conversationId, Message user, Message assistant) {
            this.requestId = request.client_request_id();
            this.question = request.question();
            this.conversationId = conversationId;
            this.user = user;
            this.assistant = assistant;
        }

        public ChatResponse response() { return response; }
    }

    public synchronized Conversation create(String title) {
        UUID id = UUID.randomUUID();
        Instant now = Instant.now();
        var conversation = new Conversation(id, title, now, now);
        conversations.put(id, conversation);
        messages.put(id, new ArrayList<>());
        return conversation;
    }

    public synchronized Conversation get(UUID id) {
        Conversation conversation = conversations.get(id);
        if (conversation == null) {
            throw new ApiException(404, "CONVERSATION_NOT_FOUND", "Không tìm thấy hội thoại.", false);
        }
        return conversation;
    }

    public synchronized PageResponse<Conversation> list(PageRequest page) {
        var sorted = conversations.values().stream().sorted(
                Comparator.comparing(Conversation::updated_at).reversed()
                        .thenComparing(c -> c.conversation_id().toString())).toList();
        return PageResponse.of(sorted, page);
    }

    public synchronized PageResponse<Message> messages(UUID id, PageRequest page) {
        get(id);
        return PageResponse.of(messages.get(id), page);
    }

    public synchronized void delete(UUID id) {
        get(id);
        checkBusy(id);
        conversations.remove(id);
        messages.remove(id);
        requests.entrySet().removeIf(entry -> {
            if (entry.getValue().conversationId.equals(id)) {
                deletedRequests.add(entry.getKey());
                return true;
            }
            return false;
        });
    }

    public synchronized Turn accept(ChatRequest request) {
        UUID requestId = request.client_request_id();
        if (deletedRequests.contains(requestId)) {
            throw new ApiException(404, "REQUEST_NOT_FOUND", "Lượt hỏi thuộc hội thoại đã xóa.", false);
        }
        Turn previous = requests.get(requestId);
        if (previous != null) {
            if (!previous.question.equals(request.question())
                    || (request.conversation_id() != null && !request.conversation_id().equals(previous.conversationId))) {
                throw new ApiException(409, "REQUEST_ID_CONFLICT", "ID lượt hỏi đã được dùng cho yêu cầu khác.", false);
            }
            if (previous.failure != null) { throw previous.failure; }
            if (previous.response != null) { return previous; }
            throw new ApiException(409, "REQUEST_IN_PROGRESS", "Lượt hỏi đang được xử lý.", true, previous.conversationId);
        }
        UUID conversationId = request.conversation_id();
        if (conversationId == null) { conversationId = create("Hội thoại mới").conversation_id(); }
        else { get(conversationId); checkBusy(conversationId); }
        List<Message> history = messages.get(conversationId);
        Instant now = Instant.now();
        var user = new Message(UUID.randomUUID(), conversationId, requestId, history.size() + 1,
                "user", "completed", request.question(), null, List.of(), null, now);
        var assistant = new Message(UUID.randomUUID(), conversationId, requestId, history.size() + 2,
                "assistant", "pending", null, null, List.of(), null, now);
        history.add(user);
        history.add(assistant);
        var turn = new Turn(request, conversationId, user, assistant);
        requests.put(requestId, turn);
        conversations.put(conversationId, get(conversationId).updated(now));
        return turn;
    }

    public synchronized ChatResponse complete(Turn turn, RagAnswer answer) {
        var response = new ChatResponse(turn.conversationId, turn.requestId, turn.user.message_id(),
                turn.assistant.message_id(), answer.status(), answer.answer(), List.copyOf(answer.citations()), turn.assistant.created_at());
        var completed = new Message(turn.assistant.message_id(), turn.conversationId, turn.requestId,
                turn.assistant.sequence_no(), "assistant", "completed", answer.answer(), answer.status(),
                response.citations(), null, turn.assistant.created_at());
        messages.get(turn.conversationId).set(turn.assistant.sequence_no() - 1, completed);
        conversations.put(turn.conversationId, get(turn.conversationId).updated(Instant.now()));
        turn.response = response;
        return response;
    }

    public synchronized ApiException fail(Turn turn, ApiException error) {
        turn.failure = error.inConversation(turn.conversationId);
        var failed = new Message(turn.assistant.message_id(), turn.conversationId, turn.requestId,
                turn.assistant.sequence_no(), "assistant", "failed", null, null, List.of(),
                error.body().error().code(), turn.assistant.created_at());
        messages.get(turn.conversationId).set(turn.assistant.sequence_no() - 1, failed);
        conversations.put(turn.conversationId, get(turn.conversationId).updated(Instant.now()));
        return turn.failure;
    }

    private void checkBusy(UUID id) {
        if (messages.get(id).stream().anyMatch(m -> m.state().equals("pending"))) {
            throw new ApiException(409, "CONVERSATION_BUSY", "Hội thoại đang xử lý một lượt hỏi.", true, id);
        }
    }
}
