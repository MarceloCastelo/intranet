#!/bin/bash
# =============================================================================
# init-letsencrypt.sh
# Emite o primeiro certificado Let's Encrypt para intranet.pedragon.com.br.
# Execute este script UMA VEZ antes de subir os containers em produção.
#
# Pré-requisitos:
#   - Docker e Docker Compose instalados
#   - Porta 80 acessível publicamente (DNS do domínio apontando para este servidor)
#   - Rodar a partir do diretório raiz do projeto
# =============================================================================

set -e

DOMAIN="intranet.pedragon.com.br"
EMAIL="francisco.pe@pedragon.com.br"          # <- Altere para o e-mail real do responsável
STAGING=0                            # 1 = modo teste (sem limite de requisições); 0 = produção
DATA_PATH="./certbot"
RSA_KEY_SIZE=4096

# ---------------------------------------------------------------------------
# Verificar se já existem certificados
# ---------------------------------------------------------------------------
if [ -d "$DATA_PATH/conf/live/$DOMAIN" ]; then
    read -rp "Certificado existente encontrado para $DOMAIN. Deseja substituir? (s/N) " RESP
    if [[ "$RESP" != "s" && "$RESP" != "S" ]]; then
        echo "Operação cancelada."
        exit 0
    fi
fi

# ---------------------------------------------------------------------------
# Baixar parâmetros TLS recomendados pelo Certbot (se ainda não existirem)
# ---------------------------------------------------------------------------
echo ">> Baixando parâmetros TLS recomendados..."
mkdir -p "$DATA_PATH/conf"

if [ ! -f "$DATA_PATH/conf/options-ssl-nginx.conf" ]; then
    curl -fsSL https://raw.githubusercontent.com/certbot/certbot/master/certbot-nginx/certbot_nginx/_internal/tls_configs/options-ssl-nginx.conf \
        -o "$DATA_PATH/conf/options-ssl-nginx.conf"
fi

if [ ! -f "$DATA_PATH/conf/ssl-dhparams.pem" ]; then
    curl -fsSL https://raw.githubusercontent.com/certbot/certbot/master/certbot/certbot/ssl-dhparams.pem \
        -o "$DATA_PATH/conf/ssl-dhparams.pem"
fi

# ---------------------------------------------------------------------------
# Criar certificado auto-assinado temporário para o Nginx conseguir iniciar
# ---------------------------------------------------------------------------
echo ">> Criando certificado temporário para $DOMAIN..."
CERT_PATH="$DATA_PATH/conf/live/$DOMAIN"
mkdir -p "$CERT_PATH"

docker compose run --rm --entrypoint "openssl req -x509 -nodes -newkey rsa:1024 -days 1 \
    -keyout /etc/letsencrypt/live/$DOMAIN/privkey.pem \
    -out    /etc/letsencrypt/live/$DOMAIN/fullchain.pem \
    -subj   '/CN=localhost'" certbot

# ---------------------------------------------------------------------------
# Iniciar Nginx com o certificado temporário
# ---------------------------------------------------------------------------
echo ">> Iniciando Nginx..."
docker compose up --force-recreate -d nginx
echo "   Aguardando Nginx inicializar..."
sleep 5

# ---------------------------------------------------------------------------
# Remover certificado temporário
# ---------------------------------------------------------------------------
echo ">> Removendo certificado temporário..."
docker compose run --rm --entrypoint "sh -c '\
    rm -rf /etc/letsencrypt/live/$DOMAIN && \
    rm -rf /etc/letsencrypt/archive/$DOMAIN && \
    rm -rf /etc/letsencrypt/renewal/$DOMAIN.conf'" certbot

# ---------------------------------------------------------------------------
# Solicitar certificado real ao Let's Encrypt
# ---------------------------------------------------------------------------
echo ">> Solicitando certificado Let's Encrypt para $DOMAIN..."

STAGING_ARG=""
if [ "$STAGING" -ne 1 ]; then
    STAGING_ARG="--staging"
    echo "   [ATENÇÃO] Modo staging ativo — certificado não será confiável pelos navegadores."
fi

docker compose run --rm --entrypoint "certbot certonly --webroot \
    -w /var/www/certbot \
    $STAGING_ARG \
    --email $EMAIL \
    --domain $DOMAIN \
    --rsa-key-size $RSA_KEY_SIZE \
    --agree-tos \
    --no-eff-email \
    --force-renewal" certbot

# ---------------------------------------------------------------------------
# Recarregar Nginx com o certificado real
# ---------------------------------------------------------------------------
echo ">> Recarregando Nginx com o certificado real..."
docker compose exec nginx nginx -s reload

echo ""
echo "=== Certificado emitido com sucesso para $DOMAIN! ==="
echo ""
echo "Para subir todos os serviços em produção, execute:"
echo "  docker compose up -d"
echo ""
echo "O container 'certbot' renovará automaticamente o certificado a cada 12 horas."
echo "Após cada renovação, recarregue o Nginx manualmente:"
echo "  docker compose exec nginx nginx -s reload"
