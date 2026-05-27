-- ============================================================
-- Migração: adiciona state_id à tabela manifestacoes
-- Executar em: portal_corporativo
-- ============================================================

USE portal_corporativo;

ALTER TABLE manifestacoes
  ADD COLUMN state_id INT NULL AFTER descricao,
  ADD CONSTRAINT fk_manifestacoes_state_id
    FOREIGN KEY (state_id) REFERENCES unit_states(id) ON DELETE SET NULL;

CREATE INDEX idx_manifestacoes_state ON manifestacoes (state_id);
