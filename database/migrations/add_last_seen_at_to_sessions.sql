-- Migration: adiciona coluna last_seen_at à tabela sessions
-- Permite rastrear o tempo de permanência do usuário no portal.
-- Execute: docker exec -i <mysql_container> mysql -u root -p portal_corporativo < database/migrations/add_last_seen_at_to_sessions.sql

USE portal_corporativo;

ALTER TABLE sessions
    ADD COLUMN last_seen_at DATETIME DEFAULT CURRENT_TIMESTAMP
        AFTER created_at;
