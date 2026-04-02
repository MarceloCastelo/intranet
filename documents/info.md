# Projeto: Portal Corporativo Interno

---

## Autenticação e Acesso

- Sistema sem cadastro público
- Login permitido apenas com e-mail corporativo
- Validação baseada no domínio do e-mail (ex: @empresa.com)

### Observação Importante
- Essa abordagem valida apenas o domínio do e-mail
- Não garante que o usuário pertence realmente à empresa
- Autenticação 2 fatores com o e-mail

### Criação de Usuários
- Apenas administradores podem criar novos usuários

---

## Segurança

### Regras de Senha
- Mínimo de 8 caracteres
- Deve conter:
  - Pelo menos 1 número
  - Pelo menos 1 caractere especial

### Armazenamento de Senhas
- Senhas devem ser armazenadas com hash seguro (ex: bcrypt)
- Nunca armazenar senhas em texto puro

### Sessão
- Controle de sessão com expiração (ex: 10 minutos de inatividade)

### Proteções obrigatórias
- CSRF
- XSS
- SQL Injection

---

## Tipos de Usuário

### Administrador
- Gerencia todo o conteúdo do site
- Pode:
  - Criar, editar e remover publicações
  - Gerenciar usuários:
    - Ativar / desativar
    - Editar
    - Remover
- Acesso ao painel administrativo

### Usuário Comum
- Apenas visualiza informações do site
- Não possui permissões de edição

### Possível Evolução
- Implementação de RBAC (Role-Based Access Control), permitindo:
  - Editor de conteúdo
  - RH
  - TI
  - Outros perfis específicos

---

## Fluxo de Login

Ao realizar login:
1. Sistema identifica o tipo de usuário
2. Se for admin:
   - Exibir tela com dois cards:
     - Painel Administrativo
     - Visualizar como usuário comum
3. Se for usuário comum:
   - Direciona direto para a página inicial

---

## Estrutura do Site

### Página Inicial
- Hero Section
  - Informações do mês (destaques)

- Seções principais
  - Últimas Notícias
  - Aniversariantes do mês:
    - Nome
    - Setor
    - Data
  - Agenda:
    - Próximos eventos

---

## Navbar Lateral

- Página Inicial
- Links
- Notícias
- Eventos
- Colaboradores

---

## Painel Administrativo

### Funcionalidades
- Gerenciamento completo de páginas:
  - Criar
  - Editar
  - Excluir conteúdo
- Gerenciamento de usuários:
  - Listar usuários
  - Ativar / desativar
  - Editar dados
  - Remover usuários

### Experiência do Administrador
- Interface simples e intuitiva
- Editor de conteúdo amigável
- Visualização (preview) antes de publicar

---

## Conteúdo Dinâmico

### Estrutura de Armazenamento
- Uso de JSON para conteúdos dinâmicos
- Permite flexibilidade e fácil manutenção

### Estratégia Recomendada
- Combinar:
  - Dados estruturados no MySQL
  - Conteúdo dinâmico em JSON

Exemplo:
- Tabela de notícias com:
  - título
  - data
  - conteúdo (JSON)

---

## Banco de Dados

- Banco: MySQL

### Estruturas principais sugeridas
- users
- news
- events
- collaborators
- logs (auditoria)

---

## Auditoria

- Registro de ações administrativas

### Informações registradas
- Usuário
- Ação realizada (create, update, delete)
- Data e hora
- Entidade afetada

---

## Upload de Arquivos

- Suporte a upload de imagens e documentos

### Regras
- Limite de tamanho
- Tipos permitidos
- Armazenamento:
  - Inicialmente local
  - Possível evolução para armazenamento externo (ex: S3)

---

## Performance

- Implementação futura de cache

### Possibilidades
- Cache de páginas principais
- Uso de Redis (opcional no futuro)

---

## Versionamento de Conteúdo

- Histórico de alterações

### Funcionalidades
- Visualizar versões anteriores
- Restaurar conteúdo antigo

---

## Infraestrutura

- Utilização de Docker
  - Container da aplicação
  - Container do banco MySQL

### Deploy
- Pode ser executado em:
  - Servidor interno
  - VPS

### Backup
- Rotina de backup do banco de dados

### Logs
- Registro de erros e atividades do sistema

---

## Observações Técnicas

- Sistema deve ser:
  - Seguro
  - Escalável
  - Fácil de manter

- Separação de responsabilidades:
  - Backend (ex: Flask)
  - Frontend
  - Banco de dados

---