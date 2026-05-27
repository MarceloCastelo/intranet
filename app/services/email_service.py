"""
Email service — envia e-mails transacionais e registra em email_logs.
"""
import logging
from datetime import datetime

from flask import current_app, render_template
from flask_mail import Message

from app import db, mail
from app.models.communication import EmailLog

logger = logging.getLogger(__name__)


def _send(recipient: str, subject: str, html: str, email_type: str) -> bool:
    """Envia um e-mail e registra o resultado em email_logs."""
    log = EmailLog(recipient=recipient, subject=subject, type=email_type)
    try:
        msg = Message(subject=subject, recipients=[recipient], html=html)
        mail.send(msg)
        log.status = 'sent'
        db.session.add(log)
        db.session.commit()
        return True
    except Exception as exc:
        logger.error('Falha ao enviar e-mail para %s: %s', recipient, exc)
        log.status = 'failed'
        log.error_message = str(exc)
        db.session.add(log)
        db.session.commit()
        return False


def send_2fa_code(user, code: str) -> bool:
    subject = f'[{current_app.config["APP_NAME"]}] Seu código de verificação'
    html = render_template('emails/2fa_code.html', user=user, code=code,
                           app_name=current_app.config['APP_NAME'])
    return _send(user.email, subject, html, '2fa')


def send_password_reset(user, reset_url: str) -> bool:
    subject = f'[{current_app.config["APP_NAME"]}] Redefinição de senha'
    html = render_template('emails/password_reset.html', user=user,
                           reset_url=reset_url, app_name=current_app.config['APP_NAME'])
    return _send(user.email, subject, html, 'password_reset')


def send_invite(user, set_password_url: str) -> bool:
    subject = f'Bem-vindo ao {current_app.config["APP_NAME"]}!'
    html = render_template('emails/invite.html', user=user,
                           set_password_url=set_password_url,
                           app_name=current_app.config['APP_NAME'])
    return _send(user.email, subject, html, 'invite')


# ─── Ouvidoria ────────────────────────────────────────────────────────────────

_TIPO_LABELS = {
    'denuncia':   'Denúncia',
    'reclamacao': 'Reclamação',
    'sugestao':   'Sugestão',
}


def _admins_for_state(state_id):
    """Retorna todos os usuários com role='rh' vinculados ao estado da manifestação."""
    from app.models.user import User
    return User.query.filter_by(role='rh', state_id=state_id, status='active').all()


def notify_ouvidoria_nova_manifestacao(manifestacao, admin_url: str) -> None:
    """Notifica por e-mail todos os admins de denúncias do estado da manifestação."""
    if not manifestacao.state_id:
        return

    admins = _admins_for_state(manifestacao.state_id)
    if not admins:
        return

    app_name    = current_app.config['APP_NAME']
    tipo_label  = _TIPO_LABELS.get(manifestacao.tipo, manifestacao.tipo)
    state_name  = manifestacao.unit_state.name if manifestacao.unit_state else ''
    data        = manifestacao.created_at.strftime('%d/%m/%Y %H:%M')
    subject     = f'[{app_name}] Nova {tipo_label} recebida — {state_name}'

    for admin in admins:
        html = render_template(
            'emails/ouvidoria_nova_manifestacao.html',
            user=admin,
            public_id=manifestacao.public_id,
            tipo_label=tipo_label,
            assunto=manifestacao.assunto,
            state_name=state_name,
            data=data,
            admin_url=admin_url,
            app_name=app_name,
        )
        _send(admin.email, subject, html, 'ouvidoria_nova')


def notify_ouvidoria_nova_resposta(manifestacao, admin_url: str) -> None:
    """Notifica por e-mail todos os admins de denúncias quando o autor responde."""
    if not manifestacao.state_id:
        return

    admins = _admins_for_state(manifestacao.state_id)
    if not admins:
        return

    app_name    = current_app.config['APP_NAME']
    tipo_label  = _TIPO_LABELS.get(manifestacao.tipo, manifestacao.tipo)
    state_name  = manifestacao.unit_state.name if manifestacao.unit_state else ''
    data        = datetime.utcnow().strftime('%d/%m/%Y %H:%M')
    subject     = f'[{app_name}] Nova mensagem do denunciante — {state_name}'

    for admin in admins:
        html = render_template(
            'emails/ouvidoria_nova_resposta.html',
            user=admin,
            public_id=manifestacao.public_id,
            tipo_label=tipo_label,
            assunto=manifestacao.assunto,
            state_name=state_name,
            data=data,
            admin_url=admin_url,
            app_name=app_name,
        )
        _send(admin.email, subject, html, 'ouvidoria_resposta')
