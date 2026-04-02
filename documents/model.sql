-- ========================================
-- DATABASE
-- ========================================
CREATE DATABASE portal_corporativo
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;
USE portal_corporativo;

-- ========================================
-- DEPARTMENTS
-- ========================================
CREATE TABLE departments (
    id         INT AUTO_INCREMENT PRIMARY KEY,
    name       VARCHAR(100) NOT NULL UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ========================================
-- USERS
-- ========================================
CREATE TABLE users (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    name            VARCHAR(150) NOT NULL,
    email           VARCHAR(150) NOT NULL UNIQUE,
    password_hash   VARCHAR(255) NOT NULL,
    role            ENUM('admin', 'user') DEFAULT 'user',
    status          ENUM('active', 'inactive') DEFAULT 'active',
    profile_picture VARCHAR(500),
    department_id   INT,
    birth_date      DATE,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    FOREIGN KEY (department_id)
        REFERENCES departments(id)
        ON DELETE SET NULL
);

-- ========================================
-- USER TOKENS (senha / convite)
-- ========================================
CREATE TABLE user_tokens (
    id         INT AUTO_INCREMENT PRIMARY KEY,
    user_id    INT          NOT NULL,
    token      VARCHAR(255) NOT NULL,
    type       ENUM('password_reset', 'invite') NOT NULL,
    expires_at DATETIME     NOT NULL,
    used_at    DATETIME     NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (user_id)
        REFERENCES users(id)
        ON DELETE CASCADE
);

CREATE UNIQUE INDEX idx_user_tokens_token ON user_tokens (token);

-- ========================================
-- PERMISSIONS (papéis granulares)
-- ========================================
CREATE TABLE permissions (
    id            INT AUTO_INCREMENT PRIMARY KEY,
    user_id       INT         NOT NULL,
    resource      VARCHAR(50) NOT NULL,   -- ex: 'news', 'pages', 'links'
    department_id INT         NULL,       -- NULL = vale para todos os departamentos
    can_create    BOOLEAN DEFAULT FALSE,
    can_edit      BOOLEAN DEFAULT FALSE,
    can_delete    BOOLEAN DEFAULT FALSE,
    can_publish   BOOLEAN DEFAULT FALSE,
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (user_id)
        REFERENCES users(id)
        ON DELETE CASCADE,

    FOREIGN KEY (department_id)
        REFERENCES departments(id)
        ON DELETE CASCADE
);

CREATE INDEX idx_permissions_user ON permissions (user_id, resource);

-- ========================================
-- CATEGORIES (categorias de notícias)
-- ========================================
CREATE TABLE categories (
    id         INT AUTO_INCREMENT PRIMARY KEY,
    name       VARCHAR(100) NOT NULL UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ========================================
-- NEWS
-- ========================================
CREATE TABLE news (
    id           INT AUTO_INCREMENT PRIMARY KEY,
    title        VARCHAR(255) NOT NULL,
    summary      VARCHAR(500),
    content_json JSON         NOT NULL,
    author_id    INT,
    is_published BOOLEAN   DEFAULT TRUE,
    published_at TIMESTAMP NULL,
    created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    FOREIGN KEY (author_id)
        REFERENCES users(id)
        ON DELETE SET NULL
);

-- ========================================
-- NEWS_CATEGORIES (junção N:N)
-- ========================================
CREATE TABLE news_categories (
    news_id     INT NOT NULL,
    category_id INT NOT NULL,

    PRIMARY KEY (news_id, category_id),

    FOREIGN KEY (news_id)
        REFERENCES news(id)
        ON DELETE CASCADE,

    FOREIGN KEY (category_id)
        REFERENCES categories(id)
        ON DELETE CASCADE
);

-- ========================================
-- COMMENTS (comentários em notícias)
-- ========================================
CREATE TABLE comments (
    id         INT AUTO_INCREMENT PRIMARY KEY,
    news_id    INT  NOT NULL,
    user_id    INT,
    content    TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    FOREIGN KEY (news_id)
        REFERENCES news(id)
        ON DELETE CASCADE,

    FOREIGN KEY (user_id)
        REFERENCES users(id)
        ON DELETE SET NULL
);

CREATE INDEX idx_comments_news ON comments (news_id);

-- ========================================
-- REACTIONS (reações em notícias)
-- ========================================
CREATE TABLE reactions (
    id         INT AUTO_INCREMENT PRIMARY KEY,
    news_id    INT         NOT NULL,
    user_id    INT         NOT NULL,
    type       VARCHAR(20) NOT NULL,   -- ex: 'like', 'love', 'clap'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    UNIQUE KEY uq_reaction (news_id, user_id, type),  -- um usuário, um tipo por notícia

    FOREIGN KEY (news_id)
        REFERENCES news(id)
        ON DELETE CASCADE,

    FOREIGN KEY (user_id)
        REFERENCES users(id)
        ON DELETE CASCADE
);

-- ========================================
-- EVENTS (AGENDA)
-- ========================================
CREATE TABLE events (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    title           VARCHAR(255) NOT NULL,
    description     JSON,
    event_date      DATE         NOT NULL,
    location        VARCHAR(255),
    created_by      INT,
    event_type      ENUM('general', 'birthday') DEFAULT 'general',
    related_user_id INT,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (created_by)
        REFERENCES users(id)
        ON DELETE SET NULL,

    FOREIGN KEY (related_user_id)
        REFERENCES users(id)
        ON DELETE CASCADE
);

-- ========================================
-- LINKS (LINKS ÚTEIS)
-- ========================================
CREATE TABLE links (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    title       VARCHAR(150) NOT NULL,
    url         VARCHAR(500) NOT NULL,
    description VARCHAR(255),
    created_by  INT,
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (created_by)
        REFERENCES users(id)
        ON DELETE SET NULL
);

-- ========================================
-- PAGES (CONTEÚDO ESTÁTICO)
-- ========================================
CREATE TABLE pages (
    id           INT AUTO_INCREMENT PRIMARY KEY,
    name         VARCHAR(100) NOT NULL UNIQUE,
    content_json JSON         NOT NULL,
    created_by   INT,
    updated_by   INT,
    created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    FOREIGN KEY (created_by)
        REFERENCES users(id)
        ON DELETE SET NULL,

    FOREIGN KEY (updated_by)
        REFERENCES users(id)
        ON DELETE SET NULL
);

-- ========================================
-- FILES (UPLOADS)
-- ========================================
CREATE TABLE files (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    file_name   VARCHAR(255) NOT NULL,
    file_path   VARCHAR(500) NOT NULL,
    file_type   VARCHAR(50),
    entity      VARCHAR(50),   -- ex: 'news', 'pages', NULL = avulso
    entity_id   INT,
    uploaded_by INT,
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (uploaded_by)
        REFERENCES users(id)
        ON DELETE SET NULL
);

CREATE INDEX idx_files_entity ON files (entity, entity_id);

-- ========================================
-- NOTIFICATIONS (NOTIFICAÇÕES)
-- ========================================
CREATE TABLE notifications (
    id         INT AUTO_INCREMENT PRIMARY KEY,
    user_id    INT          NOT NULL,
    type       VARCHAR(50)  NOT NULL,    -- ex: 'news_published', 'event_reminder'
    message    VARCHAR(500) NOT NULL,
    entity     VARCHAR(50)  NULL,        -- entidade de origem (ex: 'news')
    entity_id  INT          NULL,        -- id da entidade de origem
    read_at    DATETIME     NULL,        -- NULL = não lida
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (user_id)
        REFERENCES users(id)
        ON DELETE CASCADE
);

CREATE INDEX idx_notifications_user ON notifications (user_id, read_at);

-- ========================================
-- AUDIT LOGS (AUDITORIA)
-- ========================================
CREATE TABLE audit_logs (
    id         INT AUTO_INCREMENT PRIMARY KEY,
    user_id    INT,
    action     VARCHAR(50),
    entity     VARCHAR(50),
    entity_id  INT,
    details    JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (user_id)
        REFERENCES users(id)
        ON DELETE SET NULL
);

CREATE INDEX idx_audit_entity ON audit_logs (entity, entity_id);

-- ========================================
-- SESSIONS (CONTROLE DE SESSÃO)
-- ========================================
CREATE TABLE sessions (
    id         INT AUTO_INCREMENT PRIMARY KEY,
    user_id    INT          NOT NULL,
    token      VARCHAR(255) NOT NULL,
    expires_at DATETIME     NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (user_id)
        REFERENCES users(id)
        ON DELETE CASCADE
);

CREATE UNIQUE INDEX idx_sessions_token ON sessions (token);

-- ========================================
-- CONTENT VERSIONS (VERSIONAMENTO)
-- ========================================
CREATE TABLE content_versions (
    id             INT AUTO_INCREMENT PRIMARY KEY,
    entity         VARCHAR(50) NOT NULL,
    entity_id      INT         NOT NULL,
    content_json   JSON,
    version_number INT         NOT NULL,
    created_by     INT,
    created_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (created_by)
        REFERENCES users(id)
        ON DELETE SET NULL
);

CREATE INDEX idx_cv_entity ON content_versions (entity, entity_id);