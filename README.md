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
- ✅ Diretório de colaboradores (`/colaboradores`)
- ✅ 4 perfis: Admin, Editor, User, Viewer
- ✅ Status: Ativo, Inativo, Bloqueado
- ✅ Vínculo com departamentos
- ✅ **2FA obrigatório no primeiro login** (código por e-mail)
- ✅ Histórico de senhas (impede reutilização)
- ✅ Login com tentativas limitadas
- ✅ Sessões gerenciadas
- ✅ Validação de domínio corporativo no cadastro

### 2. Notícias e Conteúdo
- ✅ Publicação com editor rich text (TipTap)
- ✅ **Categorias + Tags** (marcadores livres)
- ✅ Slug amigável para SEO
- ✅ Imagem destacada
- ✅ **Contador de visualizações**
- ✅ Comentários (modelo polimórfico: notícias, eventos, galeria)
- ✅ 5 tipos de reações: `like`, `love`, `clap`, `laugh`, `sad` (polimórfico)
- ✅ **Workflow de aprovação** (rascunho → revisão → publicado)
- ✅ **Versionamento completo** (histórico de edições)

### 3. Conteúdo Dinâmico
- ✅ **Banners rotativos** com carrossel hero na homepage (full-bleed, auto-advance)
- ✅ Seleção de banners para exibição na tela inicial (`show_on_home`)
- ✅ **FAQ** com categorias e contador de utilidade
- ✅ **Enquetes** (múltipla escolha, expiração)
- ✅ **Galeria de imagens**
- ✅ **Newsletter** (assinaturas e envios em massa)

### 4. Agenda Corporativa
- ✅ Eventos com data/hora/local
- ✅ Tipos: Geral, Aniversário, Reunião, Treinamento, Feriado
- ✅ Links para Google Maps/Teams/Zoom
- ✅ Eventos de múltiplos dias

### 5. Menu de Serviços
- ✅ CRUD completo de serviços
- ✅ Upload de ícone por imagem (PNG, JPG, SVG, etc.)
- ✅ Ordem de exibição
- ✅ Cards responsivos com Tailwind

### 6. Colaboração
- ✅ **Favoritos** (salvar itens importantes)
- ✅ Upload de arquivos
- ✅ Notificações em tempo real

### 7. Auditoria e Métricas
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
| Comentar conteúdo | ✅ | ✅ | ✅ | ❌ |
| Excluir comentários alheios | ✅ | ❌ | ❌ | ❌ |
| Gerenciar serviços | ✅ | ✅ | ❌ | ❌ |
| Gerenciar usuários | ✅ | ❌ | ❌ | ❌ |
| Ver relatórios | ✅ | ❌ | ❌ | ❌ |

---

## 🗂️ Estrutura de Banco de Dados (35 tabelas)

### Core (6 tabelas)
- `users`, `departments`, `permissions`, `user_tokens`
- `two_factor_logs`, `password_history`

### Conteúdo (8 tabelas)
- `news`, `categories`, `tags`, `news_categories`, `news_tags`
- `news_views`, `comments` (polimórfico), `reactions` (polimórfico)
- `content_versions`

### Dinâmico (6 tabelas)
- `banners` (com `show_on_home`), `faq_categories`, `faq`
- `polls`, `poll_options`, `poll_votes`

### Colaboração (5 tabelas)
- `events`, `files`
- `galleries`, `gallery_items`, `favorites`

### Serviços (2 tabelas)
- `services`, `phone_extensions`

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

# 4. Crie usuário admin
docker-compose exec app python scripts/create_admin.py

# 6. Acesse o portal
http://localhost