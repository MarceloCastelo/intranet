-- ============================================================
-- Migração: adiciona tabela unit_states e coluna state_id em users
-- Executar em: portal_corporativo
-- ============================================================

USE portal_corporativo;

-- 1. Cria a tabela de estados de unidade
CREATE TABLE IF NOT EXISTS unit_states (
    id         INT AUTO_INCREMENT PRIMARY KEY,
    name       VARCHAR(100) NOT NULL UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. Adiciona coluna state_id à tabela de usuários
ALTER TABLE users
  ADD COLUMN state_id INT NULL AFTER department_id,
  ADD CONSTRAINT fk_users_state_id
    FOREIGN KEY (state_id) REFERENCES unit_states(id) ON DELETE SET NULL;

-- 3. Índice para melhor performance nas consultas por estado
CREATE INDEX idx_users_state ON users (state_id);
