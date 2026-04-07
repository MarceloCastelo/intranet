# Portal Corporativo - Sistema de Intranet Premium

## Visão Geral

Sistema de portal corporativo enterprise-ready com todos os recursos que um cliente pode solicitar, containerizado com Docker e preparado para escalar.

## Tecnologias Utilizadas

### Backend
- **Python 3.11** com **Flask** (Server-Side Rendering)
- **MySQL 8.0** (Banco de dados relacional exclusivo)
- **Flask-Login, Flask-WTF, SQLAlchemy**
- **Jinja2** (Template engine)

### Frontend
- **TailwindCSS** (Framework CSS utilitário)
- **HTMX + Alpine.js** (Interatividade)
- **Heroicons** (Ícones)

### DevOps
- **Docker + Docker Compose**
- **Nginx** (Proxy reverso)
- **MySQL 8.0** (Container oficial)

---

## 🎯 Funcionalidades Completas

### 1. Gestão de Usuários e Segurança
- ✅ Cadastro e gerenciamento de colaboradores
- ✅ 4 perfis: Admin, Editor, User, Viewer
- ✅ Status: Ativo, Inativo, Bloqueado
- ✅ Vínculo com departamentos
- ✅ **2FA obrigatório no primeiro login** (código por e-mail)
- ✅ Histórico de senhas (impede reutilização)
- ✅ Bloqueio de IPs suspeitos
- ✅ Login com tentativas limitadas
- ✅ Sessões gerenciadas

### 2. Notícias e Conteúdo
- ✅ Publicação com editor rich text (JSON)
- ✅ **Categorias + Tags** (marcadores livres)
- ✅ Slug amigável para SEO
- ✅ Imagem destacada
- ✅ **Contador de visualizações**
- ✅ Comentários com respostas aninhadas
- ✅ 5 tipos de reações (like, love, clap, insightful, curious)
- ✅ **Workflow de aprovação** (rascunho → revisão → publicado)
- ✅ **Versionamento completo** (histórico de edições)

### 3. Conteúdo Dinâmico
- ✅ **Banners rotativos** (homepage)
- ✅ **FAQ** com categorias e contador de utilidade
- ✅ **Enquetes** (múltipla escolha, expiração)
- ✅ **Galeria de imagens**
- ✅ **Newsletter** (assinaturas e envios em massa)

### 4. Agenda Corporativa
- ✅ Eventos com data/hora/local
- ✅ Tipos: Geral, Aniversário, Reunião, Treinamento, Feriado
- ✅ Links para Google Maps/Teams/Zoom
- ✅ Eventos de múltiplos dias

### 5. Menu de Serviços (Links)
- ✅ CRUD completo de links
- ✅ Ícones personalizados
- ✅ Ordem de exibição
- ✅ Cards responsivos com Tailwind

### 6. Páginas Estáticas
- ✅ Conteúdo gerenciável
- ✅ Versionamento
- ✅ Slug amigável

### 7. Colaboração
- ✅ **Favoritos** (salvar itens importantes)
- ✅ Upload de arquivos
- ✅ Notificações em tempo real

### 8. Auditoria e Métricas
- ✅ Logs completos de ações
- ✅ Logs de visualizações de notícias
- ✅ Logs de e-mails enviados
- ✅ Logs de tentativas de 2FA

---

## 📊 Matriz de Recursos vs Perfis

| Funcionalidade | Admin | Editor | User | Viewer |
|----------------|-------|--------|------|--------|
| Criar notícias | ✅ | ✅ | ❌ | ❌ |
| Publicar notícias | ✅ | ❌* | ❌ | ❌ |
| Gerenciar banners | ✅ | ✅ | ❌ | ❌ |
| Gerenciar FAQ | ✅ | ✅ | ❌ | ❌ |
| Criar enquetes | ✅ | ✅ | ❌ | ❌ |
| Responder enquetes | ✅ | ✅ | ✅ | ✅ |
| Gerenciar links | ✅ | ✅ | ❌ | ❌ |
| Gerenciar usuários | ✅ | ❌ | ❌ | ❌ |
| Ver relatórios | ✅ | ❌ | ❌ | ❌ |

*Editor pode criar mas precisa de aprovação do Admin

---

## 🗂️ Estrutura de Banco de Dados (33 tabelas)

### Core (7 tabelas)
- `users`, `departments`, `permissions`, `user_tokens`
- `two_factor_logs`, `password_history`, `blocked_ips`

### Conteúdo (10 tabelas)
- `news`, `categories`, `tags`, `news_categories`, `news_tags`
- `news_views`, `comments`, `reactions`
- `pages`, `content_versions`

### Dinâmico (6 tabelas)
- `banners`, `faq_categories`, `faq`
- `polls`, `poll_options`, `poll_votes`

### Colaboração (6 tabelas)
- `events`, `links`, `files`
- `galleries`, `gallery_items`, `favorites`

### Comunicação (4 tabelas)
- `subscribers`, `newsletters`, `newsletter_logs`, `email_logs`

### Auditoria (4 tabelas)
- `notifications`, `audit_logs`, `sessions`, `approval_workflow`

---

## 🚀 Instalação com Docker

### Pré-requisitos
- Docker 20.10+
- Docker Compose 2.0+

### Passo a Passo

```bash
# 1. Clone o repositório
git clone https://github.com/empresa/portal-corporativo.git
cd portal-corporativo

# 2. Configure as variáveis de ambiente
cp .env.example .env
# Edite .env com suas configurações

# 3. Inicie os containers
docker-compose up -d

# 4. Execute as migrações
docker-compose exec app flask db upgrade

# 5. Crie usuário admin
docker-compose exec app flask create-admin --email admin@empresa.com --name "Administrador"

# 6. Acesse o portal
http://localhost