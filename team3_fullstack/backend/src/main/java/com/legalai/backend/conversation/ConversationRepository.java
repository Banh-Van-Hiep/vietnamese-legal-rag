package com.legalai.backend.conversation;

import org.springframework.data.jpa.repository.JpaRepository;

/**
 * Truy cập DB cho {@link Conversation} (Spring Data JPA).
 */
public interface ConversationRepository extends JpaRepository<Conversation, Long>{

    
}
