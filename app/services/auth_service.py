"""
Auth service — toda a lógica de autenticação, 2FA e gestão de senhas.
"""
import logging
import secrets
from datetime import datetime, timedelta

from flask import current_app, request
from werkzeug.security import check_password_hash

from app import db
from app.models.audit import AuditLog
from app.models.user import PasswordHistory, TwoFactorLog, User, UserToken
from app.services.email_service import send_2fa_code, send_password_reset

logger = logging.getLogger(__name__)


# ─── Helpers ─────────────────────────────────────────────────────────────────

def _client_ip() -> str:
    return request.headers.get('X-Forwarded-For', request.remote_addr or '').split(',')[0].strip()


def _log_audit(user_id, action: str, entity: str, entity_id: int,
               old=None, new=None) -> None:
    entry = AuditLog(
        user_id=user_id, action=action, entity=entity, entity_id=entity_id,
        old_values=old, new_values=new,
        ip_address=_client_ip(), user_agent=request.headers.get('User-Agent'),
    )
    db.session.add(entry)



# ─── Login ───────────────────────────────────────────────────────────────────

def attempt_login(email: str, password: str):
    """
    Valida credenciais.

    Retorna:
        (user, error_key)
        user      — objeto User em caso de sucesso, None caso contrário
        error_key — chave de erro string ou None
    """
    user = User.query.filter_by(email=email).first()

    if not user:
        return None, 'invalid_credentials'

    if user.status == 'inactive':
        return None, 'account_inactive'

    if user.status == 'blocked':
        return None, 'account_blocked'

    if user.is_locked:
        return None, 'account_locked'

    if not user.check_password(password):
        _register_failed_attempt(user)
        return None, 'invalid_credentials'

    # Credenciais OK — zera tentativas
    user.login_attempts = 0
    user.locked_until   = None
    user.last_login_at  = datetime.utcnow()
    user.last_login_ip  = _client_ip()
    db.session.commit()
    return user, None


def _register_failed_attempt(user: User) -> None:
    max_attempts = current_app.config.get('MAX_LOGIN_ATTEMPTS', 5)
    lockout_min  = current_app.config.get('LOCKOUT_DURATION_MINUTES', 30)

    user.login_attempts += 1
    if user.login_attempts >= max_attempts:
        user.locked_until   = datetime.utcnow() + timedelta(minutes=lockout_min)
        user.login_attempts = 0
    db.session.commit()


# ─── 2FA ─────────────────────────────────────────────────────────────────────

def generate_2fa_code(user: User) -> str:
    """Cria um código numérico de 6 dígitos, persiste em user_tokens e envia por e-mail."""
    # Invalida tokens 2fa anteriores não usados
    UserToken.query.filter_by(user_id=user.id, type='2fa_email', used_at=None).delete()

    code    = ''.join(secrets.choice('0123456789') for _ in range(6))
    token   = UserToken(
        user_id    = user.id,
        token      = code,
        type       = '2fa_email',
        expires_at = datetime.utcnow() + timedelta(minutes=10),
    )
    db.session.add(token)
    db.session.commit()
    send_2fa_code(user, code)
    return code


def verify_2fa_code(user: User, code: str) -> bool:
    ip = _client_ip()
    token = UserToken.query.filter_by(
        user_id=user.id, token=code, type='2fa_email', used_at=None
    ).first()

    success = bool(token and token.expires_at > datetime.utcnow())

    log = TwoFactorLog(
        user_id        = user.id,
        success        = success,
        ip_address     = ip,
        user_agent     = request.headers.get('User-Agent'),
        failure_reason = None if success else 'invalid_or_expired_code',
    )
    db.session.add(log)

    if success:
        token.used_at = datetime.utcnow()
        # Conclui o setup obrigatório de primeiro login
        if user.two_factor_mandatory:
            user.two_factor_mandatory = False

    db.session.commit()
    return success


# ─── Senhas ───────────────────────────────────────────────────────────────────

def _password_in_history(user: User, new_password: str) -> bool:
    # Verifica senha atual
    if user.password_hash and check_password_hash(user.password_hash, new_password):
        return True
    limit  = current_app.config.get('PASSWORD_HISTORY_LIMIT', 5)
    recent = (
        PasswordHistory.query
        .filter_by(user_id=user.id)
        .order_by(PasswordHistory.changed_at.desc())
        .limit(limit)
        .all()
    )
    return any(check_password_hash(h.password_hash, new_password) for h in recent)


def change_password(user: User, new_password: str, changed_by_id: int | None = None) -> tuple[bool, str | None]:
    """
    Altera a senha do usuário.

    Retorna (True, None) em caso de sucesso
    ou (False, 'error_key') em caso de falha.
    """
    if _password_in_history(user, new_password):
        return False, 'password_reused'

    # Salva histórico antes de trocar
    history = PasswordHistory(
        user_id       = user.id,
        password_hash = user.password_hash,
        changed_by    = changed_by_id,
    )
    db.session.add(history)

    user.set_password(new_password)
    user.first_login = False
    db.session.commit()

    _log_audit(user.id, 'update', 'users', user.id,
               new={'action': 'password_changed'})
    db.session.commit()
    return True, None


# ─── Recuperação de senha ─────────────────────────────────────────────────────

def request_password_reset(email: str) -> bool:
    """Gera token e envia e-mail. Retorna True mesmo se o e-mail não existir (evita enumeração)."""
    user = User.query.filter_by(email=email).first()
    if not user or user.status != 'active':
        return True  # resposta genérica intencional

    # Invalida tokens anteriores
    UserToken.query.filter_by(user_id=user.id, type='password_reset', used_at=None).delete()

    raw_token = secrets.token_urlsafe(32)
    token = UserToken(
        user_id    = user.id,
        token      = raw_token,
        type       = 'password_reset',
        expires_at = datetime.utcnow() + timedelta(hours=2),
    )
    db.session.add(token)
    db.session.commit()

    from flask import url_for
    reset_url = url_for('auth.reset_password', token=raw_token, _external=True)
    send_password_reset(user, reset_url)
    return True


def consume_reset_token(raw_token: str):
    """Valida e retorna (user, token) ou (None, None)."""
    token = UserToken.query.filter_by(
        token=raw_token, type='password_reset', used_at=None
    ).first()
    if not token or token.expires_at < datetime.utcnow():
        return None, None
    return token.user, token


def mark_token_used(token: UserToken) -> None:
    token.used_at = datetime.utcnow()
    db.session.commit()
