import secrets
from datetime import datetime, timedelta

from flask import (Blueprint, current_app, flash, redirect, render_template,
                   request, session, url_for)
from flask_login import current_user, login_required, login_user, logout_user

from app import db
from app.forms.auth import (ChangePasswordForm, ForgotPasswordForm,
                             LoginForm, ResetPasswordForm, SetPasswordForm)
from app.models.user import Session as DbSession, User
from app.services import auth_service

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

# ─── Helpers ─────────────────────────────────────────────────────────────────

_ERROR_MESSAGES = {
    'ip_blocked':          'Acesso bloqueado. Tente novamente mais tarde.',
    'account_inactive':    'Conta desativada. Contate o administrador.',
    'account_blocked':     'Conta bloqueada. Contate o administrador.',
    'account_locked':      'Conta temporariamente bloqueada por tentativas excessivas.',
    'invalid_credentials': 'CPF ou senha inválidos.',
    'password_reused':     'Esta senha já foi usada recentemente. Escolha outra.',
    'token_invalid':       'Link inválido ou expirado.',
}


def _flash_error(key: str) -> None:
    flash(_ERROR_MESSAGES.get(key, 'Ocorreu um erro inesperado.'), 'danger')


# ─── Login / Logout ──────────────────────────────────────────────────────────

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))

    form = LoginForm()
    if form.validate_on_submit():
        user, error = auth_service.attempt_login(form.cpf.data, form.password.data)

        if error:
            _flash_error(error)
            return render_template('auth/login.html', form=form)

        # Guarda ID temporário na sessão para fluxos seguintes
        session['pending_user_id'] = user.id
        session['remember_me']     = form.remember.data

        # Primeiro login → forçar troca de senha
        if user.first_login:
            return redirect(url_for('auth.set_password'))

        # Login completo
        _complete_login(user, form.remember.data)
        return redirect(_next_safe())

    return render_template('auth/login.html', form=form)


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Você saiu com sucesso.', 'success')
    return redirect(url_for('auth.login'))


# ─── Primeiro login: definir senha ───────────────────────────────────────────

@auth_bp.route('/definir-senha', methods=['GET', 'POST'])
def set_password():
    user = _get_pending_user()
    if not user:
        return redirect(url_for('auth.login'))
    if not user.first_login:
        return redirect(url_for('main.home'))

    form = SetPasswordForm()
    if form.validate_on_submit():
        ok, error = auth_service.change_password(user, form.new_password.data, user.id)
        if not ok:
            _flash_error(error)
            return render_template('auth/set_password.html', form=form)

        flash('Senha definida com sucesso!', 'success')
        _complete_login(user, session.pop('remember_me', False))
        return redirect(_next_safe())

    return render_template('auth/set_password.html', form=form)


# ─── Alterar senha (usuário autenticado) ─────────────────────────────────────

@auth_bp.route('/alterar-senha', methods=['GET', 'POST'])
@login_required
def change_password():
    form = ChangePasswordForm()
    if form.validate_on_submit():
        if not current_user.check_password(form.current_password.data):
            flash('Senha atual incorreta.', 'danger')
            return render_template('auth/change_password.html', form=form)

        ok, error = auth_service.change_password(
            current_user, form.new_password.data, current_user.id
        )
        if not ok:
            _flash_error(error)
            return render_template('auth/change_password.html', form=form)

        flash('Senha alterada com sucesso.', 'success')
        return redirect(url_for('main.home'))

    return render_template('auth/change_password.html', form=form)


# ─── Recuperação de senha ─────────────────────────────────────────────────────

@auth_bp.route('/esqueci-senha', methods=['GET', 'POST'])
def forgot_password():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))

    form = ForgotPasswordForm()
    if form.validate_on_submit():
        auth_service.request_password_reset(form.cpf.data)
        flash('Se o CPF estiver cadastrado, você receberá as instruções no e-mail cadastrado.', 'info')
        return redirect(url_for('auth.login'))

    return render_template('auth/forgot_password.html', form=form)


@auth_bp.route('/resetar-senha/<token>', methods=['GET', 'POST'])
def reset_password(token: str):
    user, token_obj = auth_service.consume_reset_token(token)
    if not user:
        _flash_error('token_invalid')
        return redirect(url_for('auth.forgot_password'))

    # Se há um usuário logado que não é o dono do token, bloqueia
    if current_user.is_authenticated and current_user.id != user.id:
        return redirect(url_for('main.home'))

    form = ResetPasswordForm()
    if form.validate_on_submit():
        ok, error = auth_service.change_password(user, form.new_password.data)
        if not ok:
            _flash_error(error)
            return render_template('auth/reset_password.html', form=form, token=token)

        auth_service.mark_token_used(token_obj)
        flash('Senha redefinida com sucesso.', 'success')
        if current_user.is_authenticated:
            return redirect(url_for('users.profile'))
        return redirect(url_for('auth.login'))

    return render_template('auth/reset_password.html', form=form, token=token)


# ─── Utilitários privados ─────────────────────────────────────────────────────

def _get_pending_user() -> User | None:
    uid = session.get('pending_user_id')
    if not uid:
        return None
    return db.session.get(User, uid)


def _complete_login(user: User, remember: bool = False) -> None:
    login_user(user, remember=remember)
    session.pop('pending_user_id', None)
    session.pop('remember_me', None)

    # Registra sessão no banco para tracking de permanência
    lifetime = current_app.config.get('PERMANENT_SESSION_LIFETIME', timedelta(days=7))
    if isinstance(lifetime, int):
        lifetime = timedelta(seconds=lifetime)
    ip = request.headers.get('X-Forwarded-For', request.remote_addr or '').split(',')[0].strip()
    db_sess = DbSession(
        user_id    = user.id,
        token      = secrets.token_hex(32),
        ip_address = ip,
        user_agent = request.headers.get('User-Agent', '')[:512],
        expires_at = datetime.utcnow() + lifetime,
    )
    db.session.add(db_sess)
    db.session.commit()
    session['db_session_id'] = db_sess.id


def _next_safe() -> str:
    """Retorna o parâmetro ?next= somente se for uma URL relativa (evita open redirect)."""
    next_url = request.args.get('next', '')
    if next_url and next_url.startswith('/') and not next_url.startswith('//'):
        return next_url
    return url_for('main.home')
