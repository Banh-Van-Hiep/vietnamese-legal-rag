package com.legalai.backend.conversation;

import org.springframework.data.jpa.repository.JpaRepository;
import java.util.UUID;

/**
 * Placeholder for future persistence. Disabled in mock; needs a JPA entity before use.
 */
public interface ConversationRepository extends JpaRepository<Conversation, UUID>{

    
}
