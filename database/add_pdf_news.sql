-- Adiciona tipo de notícia e tabela de PDFs vinculados
ALTER TABLE news ADD COLUMN news_type VARCHAR(20) NOT NULL DEFAULT 'article';

CREATE TABLE IF NOT EXISTS news_pdfs (
    id            INT AUTO_INCREMENT PRIMARY KEY,
    news_id       INT NOT NULL,
    filename      VARCHAR(500) NOT NULL,
    original_name VARCHAR(500),
    file_path     VARCHAR(500) NOT NULL,
    created_at    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (news_id) REFERENCES news(id) ON DELETE CASCADE,
    INDEX idx_news_pdfs_news_id (news_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
