# ============================================================
# Stage 1: Compilar Tailwind CSS
# ============================================================
FROM node:20-alpine AS frontend

WORKDIR /build

COPY package.json tailwind.config.js ./
COPY app/templates ./app/templates
COPY app/static/css/input.css ./app/static/css/input.css

RUN npm install && \
    npx tailwindcss -i ./app/static/css/input.css -o ./app/static/css/output.css --minify

# ============================================================
# Stage 2: Aplicação Flask
# ============================================================
FROM python:3.11-slim AS app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Dependências de sistema necessárias para PyMySQL/cryptography
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Instalar dependências Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código da aplicação
COPY . .

# Copiar CSS compilado do stage anterior
COPY --from=frontend /build/app/static/css/output.css ./app/static/css/output.css

# Garantir que diretórios de runtime existam
RUN mkdir -p logs uploads

# Usuário não-root por segurança
RUN adduser --disabled-password --gecos "" appuser && \
    chown -R appuser:appuser /app

USER appuser

EXPOSE 5000

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "9", "--timeout", "120", "--access-logfile", "-", "wsgi:app"]
