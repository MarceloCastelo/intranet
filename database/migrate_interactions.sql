-- Migração: tornar comments e reactions polimórficos
-- Executar no container: docker exec -i portal_db mysql -u portal_user -p'NC5&z0efG%62rIUeUqFL@1fHB*f8' portal_corporativo < migrate_interactions.sql

SET FOREIGN_KEY_CHECKS = 0;

DROP TABLE IF EXISTS reactions;
DROP TABLE IF EXISTS comments;

CREATE TABLE comments (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    entity_type VARCHAR(20) NOT NULL,        -- 'news' | 'event' | 'gallery'
    entity_id   INT         NOT NULL,
    user_id     INT,
    content     TEXT        NOT NULL,
    is_approved BOOLEAN     DEFAULT TRUE,
    created_at  DATETIME    DEFAULT CURRENT_TIMESTAMP,
    updated_at  DATETIME    DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL,
    INDEX idx_comments_entity (entity_type, entity_id, is_approved, created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE reactions (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    entity_type VARCHAR(20)                                    NOT NULL,
    entity_id   INT                                            NOT NULL,
    user_id     INT                                            NOT NULL,
    emoji       ENUM('like','love','clap','laugh','sad')       DEFAULT 'like',
    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE KEY uq_reaction_entity (entity_type, entity_id, user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

SET FOREIGN_KEY_CHECKS = 1;
