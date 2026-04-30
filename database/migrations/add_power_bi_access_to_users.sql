-- Migration: adiciona coluna power_bi_access à tabela users
-- Data: 2026-04-30
-- Compatível com MySQL 8+

ALTER TABLE users
  ADD COLUMN power_bi_access TINYINT(1) NOT NULL DEFAULT 0;
