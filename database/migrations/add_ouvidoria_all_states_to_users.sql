-- ============================================================
-- Migração: adiciona campo ouvidoria_all_states em users
-- Executar em: portal_corporativo
-- ============================================================

USE portal_corporativo;

ALTER TABLE users
  ADD COLUMN ouvidoria_all_states TINYINT(1) NOT NULL DEFAULT 0
  AFTER power_bi_access;
