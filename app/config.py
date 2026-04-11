import os
from datetime import timedelta


class Config:
    # Flask
    SECRET_KEY = os.environ["SECRET_KEY"]
    WTF_CSRF_SECRET_KEY = os.environ.get("WTF_CSRF_SECRET_KEY", SECRET_KEY)

    # Banco de dados
    SQLALCHEMY_DATABASE_URI = os.environ["DATABASE_URL"]
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_recycle": 280,
        "pool_pre_ping": True,
    }

    # E-mail
    MAIL_SERVER = os.environ.get("MAIL_SERVER", "localhost")
    MAIL_PORT = int(os.environ.get("MAIL_PORT", 587))
    MAIL_USE_TLS = os.environ.get("MAIL_USE_TLS", "false").lower() == "true"
    MAIL_USE_SSL = os.environ.get("MAIL_USE_SSL", "false").lower() == "true"
    MAIL_USERNAME = os.environ.get("MAIL_USERNAME")
    MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD")
    MAIL_DEFAULT_SENDER = os.environ.get("MAIL_DEFAULT_SENDER")

    # Segurança
    MAX_LOGIN_ATTEMPTS = int(os.environ.get("MAX_LOGIN_ATTEMPTS", 5))
    LOCKOUT_DURATION_MINUTES = int(os.environ.get("LOCKOUT_DURATION_MINUTES", 30))
    PASSWORD_HISTORY_LIMIT = int(os.environ.get("PASSWORD_HISTORY_LIMIT", 5))
    PERMANENT_SESSION_LIFETIME = timedelta(
        days=int(os.environ.get("SESSION_LIFETIME_DAYS", 7))
    )

    # Cookies de sessão
    _secure_cookies = os.environ.get("SESSION_COOKIE_SECURE", "false").lower() == "true"
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE  = "Lax"
    SESSION_COOKIE_SECURE    = _secure_cookies
    REMEMBER_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_SAMESITE = "Lax"
    REMEMBER_COOKIE_SECURE   = _secure_cookies

    # Upload
    MAX_CONTENT_LENGTH = int(os.environ.get("MAX_CONTENT_LENGTH", 16 * 1024 * 1024))
    UPLOAD_FOLDER = os.environ.get("UPLOAD_FOLDER", "uploads")
    ALLOWED_EXTENSIONS = set(
        os.environ.get("ALLOWED_EXTENSIONS", "png,jpg,jpeg,gif,webp,pdf,doc,docx,xls,xlsx").split(",")
    )

    # Aplicação
    APP_NAME = os.environ.get("APP_NAME", "Portal Corporativo")
    APP_URL = os.environ.get("APP_URL", "http://localhost")
