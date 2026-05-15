-- ========================================
-- DATABASE
-- ========================================
CREATE DATABASE IF NOT EXISTS portal_corporativo
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
-- USERS (COM 2FA OBRIGATÓRIO NO PRIMEIRO LOGIN)
-- ========================================
-- USERS
-- ========================================
CREATE TABLE users (
    id                      INT AUTO_INCREMENT PRIMARY KEY,
    name                    VARCHAR(150) NOT NULL,
    cpf                     VARCHAR(11)  NOT NULL UNIQUE,
    email                   VARCHAR(150) NOT NULL UNIQUE,
    password_hash           VARCHAR(255) NOT NULL,
    role                    ENUM('user', 'editor', 'rh', 'patrimonio', 'controladoria') DEFAULT 'user',
    is_admin                BOOLEAN NOT NULL DEFAULT FALSE,
    status                  ENUM('active', 'inactive', 'blocked') DEFAULT 'active',
    profile_picture         VARCHAR(500),
    department_id           INT,
    birth_date              DATE,
    power_bi_access         TINYINT(1) NOT NULL DEFAULT 0,

    -- Primeiro acesso
    first_login             BOOLEAN DEFAULT TRUE,

    -- Segurança
    last_login_at           DATETIME NULL,
    last_login_ip           VARCHAR(45) NULL,
    login_attempts          INT DEFAULT 0,
    locked_until            DATETIME NULL,

    created_at              TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at              TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    FOREIGN KEY (department_id)
        REFERENCES departments(id)
        ON DELETE SET NULL
);

-- ========================================
-- PASSWORD HISTORY (Segurança)
-- ========================================
CREATE TABLE password_history (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    user_id         INT NOT NULL,
    password_hash   VARCHAR(255) NOT NULL,
    changed_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    changed_by      INT NULL,  -- Quem alterou (admin ou o próprio usuário)
    
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (changed_by) REFERENCES users(id) ON DELETE SET NULL,
    
    INDEX idx_password_history_user (user_id, changed_at)
);

-- ========================================
-- USER TOKENS (senha / convite / 2FA e-mail)
-- ========================================
CREATE TABLE user_tokens (
    id         INT AUTO_INCREMENT PRIMARY KEY,
    user_id    INT          NOT NULL,
    token      VARCHAR(255) NOT NULL,
    type       ENUM('password_reset', 'invite', '2fa_email') NOT NULL,
    expires_at DATETIME     NOT NULL,
    used_at    DATETIME     NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (user_id)
        REFERENCES users(id)
        ON DELETE CASCADE,
    
    UNIQUE INDEX idx_user_tokens_token (token),
    INDEX idx_user_tokens_user_type (user_id, type, used_at)
);

-- ========================================
-- 2FA LOGS
-- ========================================
CREATE TABLE two_factor_logs (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    user_id         INT,
    success         BOOLEAN NOT NULL,
    ip_address      VARCHAR(45),
    user_agent      TEXT,
    failure_reason  VARCHAR(255) NULL,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (user_id)
        REFERENCES users(id)
        ON DELETE SET NULL,
    
    INDEX idx_2fa_logs_user (user_id, created_at),
    INDEX idx_2fa_logs_ip (ip_address)
);

-- ========================================
-- PERMISSIONS (papéis granulares)
-- ========================================
CREATE TABLE permissions (
    id            INT AUTO_INCREMENT PRIMARY KEY,
    user_id       INT         NOT NULL,
    resource      VARCHAR(50) NOT NULL,   -- ex: 'news', 'pages', 'links', 'banners', 'faq', 'polls'
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
        ON DELETE CASCADE,
    
    INDEX idx_permissions_user (user_id, resource)
);

-- ========================================
-- CATEGORIES (categorias de notícias)
-- ========================================
CREATE TABLE categories (
    id         INT AUTO_INCREMENT PRIMARY KEY,
    name       VARCHAR(100) NOT NULL UNIQUE,
    slug       VARCHAR(100) NOT NULL UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ========================================
-- TAGS (marcadores livres)
-- ========================================
CREATE TABLE tags (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    name        VARCHAR(50) NOT NULL UNIQUE,
    slug        VARCHAR(50) NOT NULL UNIQUE,
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ========================================
-- NEWS
-- ========================================
CREATE TABLE news (
    id           INT AUTO_INCREMENT PRIMARY KEY,
    title        VARCHAR(255) NOT NULL,
    slug         VARCHAR(255) NOT NULL UNIQUE,
    summary      VARCHAR(500),
    content_json JSON         NOT NULL,
    featured_image VARCHAR(500),
    author_id    INT,
    is_published BOOLEAN   DEFAULT FALSE,
    published_at TIMESTAMP NULL,
    views_count  INT DEFAULT 0,
    created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    FOREIGN KEY (author_id)
        REFERENCES users(id)
        ON DELETE SET NULL,
    
    INDEX idx_news_published (is_published, published_at),
    INDEX idx_news_slug (slug)
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
-- NEWS_TAGS (junção N:N)
-- ========================================
CREATE TABLE news_tags (
    news_id     INT NOT NULL,
    tag_id      INT NOT NULL,
    
    PRIMARY KEY (news_id, tag_id),
    
    FOREIGN KEY (news_id)
        REFERENCES news(id)
        ON DELETE CASCADE,
    
    FOREIGN KEY (tag_id)
        REFERENCES tags(id)
        ON DELETE CASCADE
);

-- ========================================
-- NEWS_VIEWS (log de visualizações)
-- ========================================
CREATE TABLE news_views (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    news_id     INT NOT NULL,
    user_id     INT NULL,  -- NULL = visitante não logado
    ip_address  VARCHAR(45),
    viewed_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (news_id)
        REFERENCES news(id)
        ON DELETE CASCADE,
    
    FOREIGN KEY (user_id)
        REFERENCES users(id)
        ON DELETE SET NULL,
    
    INDEX idx_news_views_count (news_id, viewed_at),
    INDEX idx_news_views_user (user_id, viewed_at)
);

-- ========================================
-- COMMENTS (polimórfico: news, event, gallery)
-- ========================================
CREATE TABLE comments (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    entity_type VARCHAR(20)  NOT NULL,   -- 'news' | 'event' | 'gallery'
    entity_id   INT          NOT NULL,
    user_id     INT,
    content     TEXT NOT NULL,
    is_approved BOOLEAN DEFAULT TRUE,
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    FOREIGN KEY (user_id)
        REFERENCES users(id)
        ON DELETE SET NULL,

    INDEX idx_comments_entity (entity_type, entity_id, is_approved, created_at)
);

-- ========================================
-- REACTIONS (polimórfico: news, event, gallery)
-- ========================================
CREATE TABLE reactions (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    entity_type VARCHAR(20) NOT NULL,   -- 'news' | 'event' | 'gallery'
    entity_id   INT         NOT NULL,
    user_id     INT         NOT NULL,
    emoji       ENUM('like', 'love', 'clap', 'laugh', 'sad') DEFAULT 'like',
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    UNIQUE KEY uq_reaction_entity (entity_type, entity_id, user_id),

    FOREIGN KEY (user_id)
        REFERENCES users(id)
        ON DELETE CASCADE
);

-- ========================================
-- BANNERS (homepage dinâmica)
-- ========================================
CREATE TABLE banners (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    title           VARCHAR(100),
    description     TEXT,
    image_path      VARCHAR(500) NOT NULL,
    link_url        VARCHAR(500),
    link_text       VARCHAR(50),
    order_position  INT DEFAULT 0,
    is_active       BOOLEAN DEFAULT TRUE,
    show_on_home    BOOLEAN DEFAULT FALSE,
    start_date      DATE,
    end_date        DATE,
    target_blank    BOOLEAN DEFAULT TRUE,
    created_by      INT,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (created_by)
        REFERENCES users(id)
        ON DELETE SET NULL,
    
    INDEX idx_banners_active (is_active, start_date, end_date),
    INDEX idx_banners_order (order_position)
);

-- ========================================
-- FAQ (Perguntas Frequentes)
-- ========================================
CREATE TABLE faq_categories (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    name            VARCHAR(100) NOT NULL,
    description     TEXT,
    order_position  INT DEFAULT 0,
    is_active       BOOLEAN DEFAULT TRUE,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE faq (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    category_id     INT,
    question        VARCHAR(255) NOT NULL,
    answer          TEXT NOT NULL,
    order_position  INT DEFAULT 0,
    is_active       BOOLEAN DEFAULT TRUE,
    views_count     INT DEFAULT 0,
    helpful_count   INT DEFAULT 0,
    not_helpful_count INT DEFAULT 0,
    created_by      INT,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (category_id)
        REFERENCES faq_categories(id)
        ON DELETE SET NULL,
    
    FOREIGN KEY (created_by)
        REFERENCES users(id)
        ON DELETE SET NULL,
    
    INDEX idx_faq_active (is_active, order_position)
);

-- ========================================
-- POLLS (Enquetes)
-- ========================================
CREATE TABLE polls (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    question    VARCHAR(255) NOT NULL,
    description TEXT,
    is_active   BOOLEAN DEFAULT TRUE,
    is_multiple  BOOLEAN DEFAULT FALSE,  -- Permitir múltiplas escolhas
    created_by  INT,
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at  DATETIME NULL,
    
    FOREIGN KEY (created_by)
        REFERENCES users(id)
        ON DELETE SET NULL,
    
    INDEX idx_polls_active (is_active, expires_at)
);

CREATE TABLE poll_options (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    poll_id     INT NOT NULL,
    option_text VARCHAR(255) NOT NULL,
    order_position INT DEFAULT 0,
    
    FOREIGN KEY (poll_id)
        REFERENCES polls(id)
        ON DELETE CASCADE,
    
    INDEX idx_poll_options_poll (poll_id)
);

CREATE TABLE poll_votes (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    poll_id     INT NOT NULL,
    option_id   INT NOT NULL,
    user_id     INT NOT NULL,
    voted_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (poll_id)
        REFERENCES polls(id),
    
    FOREIGN KEY (option_id)
        REFERENCES poll_options(id),
    
    FOREIGN KEY (user_id)
        REFERENCES users(id),
    
    UNIQUE KEY uq_user_poll (user_id, poll_id),  -- 1 voto por enquete
    INDEX idx_poll_votes_option (option_id)
);

-- ========================================
-- EVENTS (AGENDA)
-- ========================================
CREATE TABLE events (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    title           VARCHAR(255) NOT NULL,
    description     JSON,
    event_date      DATE NOT NULL,
    event_time      TIME NULL,
    end_date        DATE NULL,  -- Para eventos com múltiplos dias
    location        VARCHAR(255),
    location_url    VARCHAR(500),  -- Link para Google Maps/Teams/Zoom
    created_by      INT,
    event_type      ENUM('general', 'birthday', 'meeting', 'training', 'holiday') DEFAULT 'general',
    related_user_id INT,
    is_active       BOOLEAN DEFAULT TRUE,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    FOREIGN KEY (created_by)
        REFERENCES users(id)
        ON DELETE SET NULL,

    FOREIGN KEY (related_user_id)
        REFERENCES users(id)
        ON DELETE CASCADE,
    
    INDEX idx_events_date (event_date, is_active),
    INDEX idx_events_type (event_type)
);

-- ========================================
-- PHONE EXTENSIONS (RAMAIS)
-- ========================================
CREATE TABLE phone_extensions (
    id             INT AUTO_INCREMENT PRIMARY KEY,
    name           VARCHAR(150) NOT NULL,
    extension      VARCHAR(20)  NOT NULL,
    department_id  INT,
    user_id        INT,
    notes          VARCHAR(255),
    order_position INT DEFAULT 0,
    is_active      BOOLEAN DEFAULT TRUE,
    created_by     INT,
    created_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    FOREIGN KEY (department_id) REFERENCES departments(id) ON DELETE SET NULL,
    FOREIGN KEY (user_id)       REFERENCES users(id)       ON DELETE SET NULL,
    FOREIGN KEY (created_by)    REFERENCES users(id)       ON DELETE SET NULL,

    INDEX idx_extensions_active (is_active, order_position)
);

-- ========================================
-- SERVICES (SERVIÇOS / FERRAMENTAS)
-- ========================================
CREATE TABLE services (
    id             INT AUTO_INCREMENT PRIMARY KEY,
    title          VARCHAR(150) NOT NULL,
    url            VARCHAR(500) NOT NULL,
    description    VARCHAR(255),
    category       VARCHAR(100) DEFAULT 'Geral',
    color          VARCHAR(30)  DEFAULT 'blue',
    icon_url       VARCHAR(500),
    target_blank   BOOLEAN DEFAULT TRUE,
    order_position INT DEFAULT 0,
    is_active      BOOLEAN DEFAULT TRUE,
    created_by     INT,
    created_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL,

    INDEX idx_services_active (is_active, category, order_position)
);

-- ========================================
-- LINKS (LINKS ÚTEIS - MENU DE SERVIÇOS)
-- ========================================
CREATE TABLE links (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    title       VARCHAR(150) NOT NULL,
    url         VARCHAR(500) NOT NULL,
    description VARCHAR(255),
    icon_class  VARCHAR(50),  -- Classe do ícone (ex: 'fas fa-user')
    target_blank BOOLEAN DEFAULT TRUE,
    order_position INT DEFAULT 0,
    is_active   BOOLEAN DEFAULT TRUE,
    created_by  INT,
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    FOREIGN KEY (created_by)
        REFERENCES users(id)
        ON DELETE SET NULL,
    
    INDEX idx_links_active (is_active, order_position)
);

-- ========================================
-- FILES (UPLOADS)
-- ========================================
CREATE TABLE files (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    file_name   VARCHAR(255) NOT NULL,
    file_original_name VARCHAR(255) NOT NULL,
    file_path   VARCHAR(500) NOT NULL,
    file_size   INT,  -- Tamanho em bytes
    file_type   VARCHAR(50),  -- MIME type
    entity      VARCHAR(50),  -- ex: 'news', 'pages', 'banners', NULL = avulso
    entity_id   INT,
    uploaded_by INT,
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (uploaded_by)
        REFERENCES users(id)
        ON DELETE SET NULL,
    
    INDEX idx_files_entity (entity, entity_id),
    INDEX idx_files_uploader (uploaded_by)
);

-- ========================================
-- GALLERIES (Galeria de imagens)
-- ========================================
CREATE TABLE galleries (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    title       VARCHAR(255) NOT NULL,
    description TEXT,
    cover_image VARCHAR(500),
    created_by  INT,
    is_active   BOOLEAN DEFAULT TRUE,
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (created_by)
        REFERENCES users(id)
        ON DELETE SET NULL,
    
    INDEX idx_galleries_active (is_active)
);

CREATE TABLE gallery_items (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    gallery_id      INT NOT NULL,
    image_path      VARCHAR(500) NOT NULL,
    thumbnail_path  VARCHAR(500),
    caption         VARCHAR(255),
    order_position  INT DEFAULT 0,
    
    FOREIGN KEY (gallery_id)
        REFERENCES galleries(id)
        ON DELETE CASCADE,
    
    INDEX idx_gallery_items_order (gallery_id, order_position)
);

-- ========================================
-- NEWSLETTERS (Assinaturas e envios)
-- ========================================
CREATE TABLE subscribers (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    email           VARCHAR(150) NOT NULL UNIQUE,
    name            VARCHAR(150),
    is_active       BOOLEAN DEFAULT TRUE,
    subscribed_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    unsubscribed_at DATETIME NULL,
    unsubscribe_token VARCHAR(255),
    
    INDEX idx_subscribers_active (is_active, subscribed_at)
);

CREATE TABLE newsletters (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    subject     VARCHAR(255) NOT NULL,
    content     JSON NOT NULL,
    status      ENUM('draft', 'sent', 'failed') DEFAULT 'draft',
    sent_at     DATETIME NULL,
    total_sent  INT DEFAULT 0,
    total_opened INT DEFAULT 0,
    created_by  INT,
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (created_by)
        REFERENCES users(id)
        ON DELETE SET NULL,
    
    INDEX idx_newsletters_status (status, sent_at)
);

CREATE TABLE newsletter_logs (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    newsletter_id   INT NOT NULL,
    subscriber_id   INT NOT NULL,
    status          ENUM('sent', 'opened', 'failed') DEFAULT 'sent',
    sent_at         TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    opened_at       DATETIME NULL,
    error_message   TEXT NULL,
    
    FOREIGN KEY (newsletter_id)
        REFERENCES newsletters(id)
        ON DELETE CASCADE,
    
    FOREIGN KEY (subscriber_id)
        REFERENCES subscribers(id),
    
    INDEX idx_newsletter_logs (newsletter_id, status)
);

-- ========================================
-- FAVORITES (Itens salvos pelos usuários)
-- ========================================
CREATE TABLE favorites (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    user_id     INT NOT NULL,
    entity      VARCHAR(50) NOT NULL,  -- 'news', 'link', 'event', 'faq'
    entity_id   INT NOT NULL,
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (user_id)
        REFERENCES users(id)
        ON DELETE CASCADE,
    
    UNIQUE KEY uq_user_favorite (user_id, entity, entity_id),
    INDEX idx_favorites_user (user_id, created_at)
);

-- ========================================
-- APPROVAL WORKFLOW — legado (mantido para compatibilidade)
-- ========================================
CREATE TABLE approval_workflow (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    entity      VARCHAR(50) NOT NULL,
    entity_id   INT NOT NULL,
    requested_by INT,
    approved_by INT NULL,
    status      ENUM('pending', 'approved', 'rejected', 'revised') DEFAULT 'pending',
    comments    TEXT,
    requested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    approved_at DATETIME NULL,

    FOREIGN KEY (requested_by) REFERENCES users(id),
    FOREIGN KEY (approved_by)  REFERENCES users(id),

    INDEX idx_approval_entity  (entity, entity_id, status),
    INDEX idx_approval_pending (status, requested_at)
);

-- ========================================
-- CONTENT APPROVALS (fila de aprovação de editores)
-- ========================================
CREATE TABLE content_approvals (
    id               INT AUTO_INCREMENT PRIMARY KEY,
    action           ENUM('publish', 'unpublish', 'edit', 'delete') NOT NULL,
    content_type     ENUM('news', 'page', 'event', 'faq', 'poll', 'gallery', 'extension', 'service', 'banner') NOT NULL,
    content_id       INT NOT NULL,
    requested_by_id  INT,
    requested_at     DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    status           ENUM('pending', 'approved', 'rejected') NOT NULL DEFAULT 'pending',
    reviewed_by_id   INT,
    reviewed_at      DATETIME NULL,
    review_note      TEXT NULL,
    snapshot         JSON NULL,
    content_title    VARCHAR(255) NULL,

    FOREIGN KEY (requested_by_id) REFERENCES users(id) ON DELETE SET NULL,
    FOREIGN KEY (reviewed_by_id)  REFERENCES users(id) ON DELETE SET NULL,

    INDEX idx_approvals_status  (status, requested_at),
    INDEX idx_approvals_content (content_type, content_id)
);

-- ========================================
-- SITE MODULES (ativação de módulos da intranet)
-- ========================================
CREATE TABLE site_modules (
    `key`     VARCHAR(50) PRIMARY KEY,
    name      VARCHAR(100) NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE
);

-- ========================================
-- OUVIDORIA
-- ========================================
CREATE TABLE manifestacoes (
    id         INT AUTO_INCREMENT PRIMARY KEY,
    public_id  VARCHAR(32) NOT NULL,
    tipo       ENUM('denuncia', 'reclamacao', 'sugestao') NOT NULL,
    assunto    VARCHAR(200) NOT NULL,
    descricao  TEXT NOT NULL,
    status     ENUM('pendente', 'em_andamento', 'concluida', 'arquivada') NOT NULL DEFAULT 'pendente',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    UNIQUE KEY uq_manifestacoes_public_id (public_id),
    INDEX idx_manifestacoes_public_id (public_id)
);

CREATE TABLE manifestacao_respostas (
    id               INT AUTO_INCREMENT PRIMARY KEY,
    manifestacao_id  INT NOT NULL,
    respondente_id   INT,
    conteudo         TEXT NOT NULL,
    origem           ENUM('responsavel', 'autor') NOT NULL DEFAULT 'responsavel',
    status_anterior  VARCHAR(20) NOT NULL,
    status_novo      VARCHAR(20) NOT NULL,
    created_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (manifestacao_id) REFERENCES manifestacoes(id) ON DELETE CASCADE,
    FOREIGN KEY (respondente_id)  REFERENCES users(id)         ON DELETE SET NULL
);

-- ========================================
-- NOTIFICATIONS
-- ========================================
CREATE TABLE notifications (
    id         INT AUTO_INCREMENT PRIMARY KEY,
    user_id    INT          NOT NULL,
    type       VARCHAR(50)  NOT NULL,  -- 'news_published', 'event_reminder', '2fa_enabled', 'approval_pending'
    message    VARCHAR(500) NOT NULL,
    entity     VARCHAR(50)  NULL,
    entity_id  INT          NULL,
    read_at    DATETIME     NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (user_id)
        REFERENCES users(id)
        ON DELETE CASCADE,
    
    INDEX idx_notifications_user (user_id, read_at, created_at)
);

-- ========================================
-- AUDIT LOGS
-- ========================================
CREATE TABLE audit_logs (
    id         INT AUTO_INCREMENT PRIMARY KEY,
    user_id    INT,
    action     VARCHAR(50),  -- 'create', 'update', 'delete', 'publish', 'approve'
    entity     VARCHAR(50),
    entity_id  INT,
    old_values JSON,
    new_values JSON,
    ip_address VARCHAR(45),
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (user_id)
        REFERENCES users(id)
        ON DELETE SET NULL,
    
    INDEX idx_audit_entity (entity, entity_id, created_at),
    INDEX idx_audit_user (user_id, created_at),
    INDEX idx_audit_action (action, created_at)
);

-- ========================================
-- SESSIONS
-- ========================================
CREATE TABLE sessions (
    id           INT AUTO_INCREMENT PRIMARY KEY,
    user_id      INT          NOT NULL,
    token        VARCHAR(255) NOT NULL,
    ip_address   VARCHAR(45),
    user_agent   TEXT,
    expires_at   DATETIME     NOT NULL,
    created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_seen_at DATETIME  DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (user_id)
        REFERENCES users(id)
        ON DELETE CASCADE,
    
    UNIQUE INDEX idx_sessions_token (token),
    INDEX idx_sessions_user (user_id, expires_at)
);

-- ========================================
-- CONTENT VERSIONS (Versionamento)
-- ========================================
CREATE TABLE content_versions (
    id             INT AUTO_INCREMENT PRIMARY KEY,
    entity         VARCHAR(50) NOT NULL,  -- 'news', 'page'
    entity_id      INT         NOT NULL,
    content_json   JSON,
    version_number INT         NOT NULL,
    created_by     INT,
    created_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (created_by)
        REFERENCES users(id)
        ON DELETE SET NULL,
    
    UNIQUE KEY uq_entity_version (entity, entity_id, version_number),
    INDEX idx_cv_entity (entity, entity_id, created_at)
);

-- ========================================
-- SISTEMA DE LOGS DE EMAIL
-- ========================================
CREATE TABLE email_logs (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    recipient   VARCHAR(150) NOT NULL,
    subject     VARCHAR(255) NOT NULL,
    type        VARCHAR(50),  -- '2fa', 'password_reset', 'invite', 'newsletter'
    status      ENUM('sent', 'failed', 'opened') DEFAULT 'sent',
    error_message TEXT,
    sent_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    opened_at   DATETIME NULL,
    
    INDEX idx_email_logs_recipient (recipient, sent_at),
    INDEX idx_email_logs_type (type, sent_at)
);

-- ========================================
-- ÍNDICES ADICIONAIS PARA PERFORMANCE
-- ========================================
CREATE INDEX idx_users_status ON users(status, role);
CREATE INDEX idx_users_department ON users(department_id, status);
CREATE INDEX idx_users_cpf ON users(cpf);
CREATE INDEX idx_news_author ON news(author_id, created_at);
CREATE INDEX idx_comments_approved ON comments(entity_type, entity_id, is_approved, created_at);
CREATE INDEX idx_events_upcoming ON events(event_date, is_active);
CREATE INDEX idx_polls_expires ON polls(is_active, expires_at);