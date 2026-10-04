package com.legalai.backend.conversation;

import org.springframework.data.jpa.repository.JpaRepository;

/**
 * Truy cập DB cho {@link Message} (Spring Data JPA).
 */
public interface MessageRepository extends JpaRepository<Message, Long>{

}
