-- ========================================
-- DATABASE
-- ========================================
CREATE DATABASE portal_corporativo;
USE portal_corporativo;

-- ========================================
-- USERS
-- ========================================
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(150) NOT NULL,
    email VARCHAR(150) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role ENUM('admin', 'user') DEFAULT 'user',
    status ENUM('active', 'inactive') DEFAULT 'active',
    profile_picture VARCHAR(500),
    department VARCHAR(100),
    birth_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- ========================================
-- NEWS (NOTÍCIAS)
-- ========================================
CREATE TABLE news (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    summary VARCHAR(500),
    content_json JSON NOT NULL,
    author_id INT,
    is_published BOOLEAN DEFAULT TRUE,
    published_at TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    FOREIGN KEY (author_id) REFERENCES users(id)
);

-- ========================================
-- EVENTS (EVENTOS / AGENDA)
-- ========================================
CREATE TABLE events (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    description JSON,
    event_date DATE NOT NULL,
    location VARCHAR(255),
    created_by INT,

    -- DIFERENCIAR TIPOS DE EVENTO
    event_type ENUM('general', 'birthday') DEFAULT 'general',

    -- RELAÇÃO OPCIONAL COM USUÁRIO (para aniversários)
    related_user_id INT,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (created_by) REFERENCES users(id),
    FOREIGN KEY (related_user_id) REFERENCES users(id)
);

-- ========================================
-- LINKS (LINKS ÚTEIS)
-- ========================================
CREATE TABLE links (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(150) NOT NULL,
    url VARCHAR(500) NOT NULL,
    description VARCHAR(255),
    created_by INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (created_by) REFERENCES users(id)
);

-- ========================================
-- PAGES (CONTEÚDO DINÂMICO EM JSON)
-- ========================================
CREATE TABLE pages (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    content_json JSON NOT NULL,
    updated_by INT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    FOREIGN KEY (updated_by) REFERENCES users(id)
);

-- ========================================
-- AUDIT LOGS (AUDITORIA)
-- ========================================
CREATE TABLE audit_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    action VARCHAR(50),
    entity VARCHAR(50),
    entity_id INT,
    details JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- ========================================
-- SESSIONS (CONTROLE DE SESSÃO)
-- ========================================
CREATE TABLE sessions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    token VARCHAR(255) NOT NULL,
    expires_at DATETIME NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- ========================================
-- FILES (UPLOADS)
-- ========================================
CREATE TABLE files (
    id INT AUTO_INCREMENT PRIMARY KEY,
    file_name VARCHAR(255),
    file_path VARCHAR(500),
    file_type VARCHAR(50),
    uploaded_by INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (uploaded_by) REFERENCES users(id)
);

-- ========================================
-- VERSIONAMENTO DE CONTEÚDO
-- ========================================
CREATE TABLE content_versions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    entity VARCHAR(50),
    entity_id INT,
    content_json JSON,
    version_number INT,
    created_by INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (created_by) REFERENCES users(id)
);