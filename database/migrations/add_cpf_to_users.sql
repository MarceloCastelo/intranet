-- ============================================================
-- Migração: adiciona CPF ao usuário e remove fluxo de 2FA
-- Executar em: portal_corporativo
-- ============================================================

USE portal_corporativo;

-- 1. Adiciona coluna cpf (nullable primeiro para preencher dados existentes)
ALTER TABLE users
  ADD COLUMN cpf VARCHAR(11) NULL AFTER name;

-- 2. Preenche CPF temporário para linhas existentes (ajustar manualmente depois)
--    Usa o ID do usuário como placeholder — deve ser atualizado antes de aplicar NOT NULL
UPDATE users SET cpf = LPAD(id, 11, '0') WHERE cpf IS NULL;

-- 3. Aplica NOT NULL e índice único
ALTER TABLE users
  MODIFY COLUMN cpf VARCHAR(11) NOT NULL,
  ADD UNIQUE INDEX idx_users_cpf (cpf);

-- 4. Remove colunas de 2FA que não são mais utilizadas
ALTER TABLE users
  DROP COLUMN IF EXISTS two_factor_enabled,
  DROP COLUMN IF EXISTS two_factor_mandatory;
