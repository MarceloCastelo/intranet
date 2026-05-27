-- ============================================================
-- Migração: cria tabela site_config (configurações globais)
-- Executar em: portal_corporativo
-- ============================================================

CREATE TABLE IF NOT EXISTS `site_config` (
    `key`   VARCHAR(100) NOT NULL,
    `value` TEXT,
    PRIMARY KEY (`key`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
