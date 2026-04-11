from datetime import datetime, timezone

from flask import (Blueprint, flash, redirect, render_template,
                   request, session, url_for)
from flask_login import current_user, login_required, login_user, logout_user

from app import db
from app.forms.auth import (ChangePasswordForm, ForgotPasswordForm,
                             LoginForm, ResetPasswordForm, SetPasswordForm,
                             TwoFactorForm)
from app.models.user import User
from app.services import auth_service

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

# ─── Helpers ─────────────────────────────────────────────────────────────────

_ERROR_MESSAGES = {
    'ip_blocked':          'Acesso bloqueado. Tente novamente mais tarde.',
    'account_inactive':    'Conta desativada. Contate o administrador.',
    'account_blocked':     'Conta bloqueada. Contate o administrador.',
    'account_locked':      'Conta temporariamente bloqueada por tentativas excessivas.',
    'invalid_credentials': 'E-mail ou senha inválidos.',
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
        user, error = auth_service.attempt_login(form.email.data, form.password.data)

        if error:
            _flash_error(error)
            return render_template('auth/login.html', form=form)

        # Guarda ID temporário na sessão para o fluxo de 2FA
        session['pending_user_id'] = user.id
        session['remember_me']     = form.remember.data

        # Primeiro login → forçar troca de senha antes do 2FA
        if user.first_login:
            return redirect(url_for('auth.set_password'))

        # 2FA obrigatório
        if user.two_factor_mandatory or user.two_factor_enabled:
            auth_service.generate_2fa_code(user)
            return redirect(url_for('auth.two_factor'))

        # Sem 2FA (viewer sem obrigatoriedade)
        _complete_login(user, form.remember.data)
        return redirect(_next_safe())

    return render_template('auth/login.html', form=form)


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Você saiu com sucesso.', 'success')
    return redirect(url_for('auth.login'))


# ─── 2FA ─────────────────────────────────────────────────────────────────────

@auth_bp.route('/2fa', methods=['GET', 'POST'])
def two_factor():
    user = _get_pending_user()
    if not user:
        return redirect(url_for('auth.login'))

    form = TwoFactorForm()
    if form.validate_on_submit():
        if auth_service.verify_2fa_code(user, form.code.data.strip()):
            remember = session.pop('remember_me', False)
            _complete_login(user, remember)
            return redirect(_next_safe())
        flash('Código inválido ou expirado.', 'danger')

    return render_template('auth/two_factor.html', form=form, email=user.email)


@auth_bp.route('/2fa/reenviar')
def resend_2fa():
    user = _get_pending_user()
    if not user:
        return redirect(url_for('auth.login'))

    # Rate limit: no máximo 1 reenvio a cada 60 segundos
    last_resend = session.get('2fa_last_resend')
    now = datetime.now(timezone.utc).timestamp()
    if last_resend and (now - last_resend) < 60:
        flash('Aguarde 60 segundos antes de solicitar novo código.', 'warning')
        return redirect(url_for('auth.two_factor'))

    session['2fa_last_resend'] = now
    auth_service.generate_2fa_code(user)
    flash('Novo código enviado para seu e-mail.', 'info')
    return redirect(url_for('auth.two_factor'))


# ─── Primeiro login: definir senha ───────────────────────────────────────────

@auth_bp.route('/definir-senha', methods=['GET', 'POST'])
def set_password():
    user = _get_pending_user()
    if not user:
        return redirect(url_for('auth.login'))
    if not user.first_login:
        return redirect(url_for('auth.two_factor'))

    form = SetPasswordForm()
    if form.validate_on_submit():
        ok, error = auth_service.change_password(user, form.new_password.data, user.id)
        if not ok:
            _flash_error(error)
            return render_template('auth/set_password.html', form=form)

        flash('Senha definida com sucesso. Verifique seu e-mail para continuar.', 'success')
        if user.two_factor_mandatory or user.two_factor_enabled:
            auth_service.generate_2fa_code(user)
            return redirect(url_for('auth.two_factor'))
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
        auth_service.request_password_reset(form.email.data)
        flash('Se o e-mail estiver cadastrado, você receberá as instruções em breve.', 'info')
        return redirect(url_for('auth.login'))

    return render_template('auth/forgot_password.html', form=form)


@auth_bp.route('/resetar-senha/<token>', methods=['GET', 'POST'])
def reset_password(token: str):
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))

    user, token_obj = auth_service.consume_reset_token(token)
    if not user:
        _flash_error('token_invalid')
        return redirect(url_for('auth.forgot_password'))

    form = ResetPasswordForm()
    if form.validate_on_submit():
        ok, error = auth_service.change_password(user, form.new_password.data)
        if not ok:
            _flash_error(error)
            return render_template('auth/reset_password.html', form=form, token=token)

        auth_service.mark_token_used(token_obj)
        flash('Senha redefinida com sucesso. Faça login.', 'success')
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


def _next_safe() -> str:
    """Retorna o parâmetro ?next= somente se for uma URL relativa (evita open redirect)."""
    next_url = request.args.get('next', '')
    if next_url and next_url.startswith('/') and not next_url.startswith('//'):
        return next_url
    return url_for('main.home')
