"""
User service — criação, edição, convite e gestão de usuários.
"""
import logging
import os
import secrets
import uuid
from datetime import datetime, timedelta

from flask import current_app
from PIL import Image
from werkzeug.exceptions import BadRequest
from werkzeug.utils import secure_filename

from app import db
from app.models.audit import AuditLog, Notification
from app.models.user import Department, User, UserToken
from app.services.email_service import send_invite

logger = logging.getLogger(__name__)

_ALLOWED_AVATAR_EXTS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

# ─── Helpers ─────────────────────────────────────────────────────────────────

def _save_profile_picture(file_storage, old_path: str | None = None) -> str:
    """Redimensiona e salva a foto de perfil. Retorna o caminho relativo."""
    upload_dir = os.path.join(current_app.root_path, '..', 'uploads', 'avatars')
    os.makedirs(upload_dir, exist_ok=True)

    ext = secure_filename(file_storage.filename).rsplit('.', 1)[-1].lower()
    if ext not in _ALLOWED_AVATAR_EXTS:
        raise BadRequest(f'Tipo de arquivo não permitido para foto de perfil: .{ext}')
    filename = f"{uuid.uuid4().hex}.{ext}"
    dest     = os.path.join(upload_dir, filename)

    img = Image.open(file_storage)
    img.thumbnail((256, 256))
    img.save(dest)

    # Remove foto anterior
    if old_path:
        old_abs = os.path.join(current_app.root_path, '..', old_path.lstrip('/'))
        if os.path.isfile(old_abs):
            os.remove(old_abs)

    return f'/uploads/avatars/{filename}'


# Alias público
save_profile_picture = _save_profile_picture


def _audit(actor_id, action: str, entity_id: int, old=None, new=None) -> None:
    entry = AuditLog(
        user_id=actor_id, action=action,
        entity='users', entity_id=entity_id,
        old_values=old, new_values=new,
    )
    db.session.add(entry)


# ─── Listagem / busca ─────────────────────────────────────────────────────────

def list_users(search: str = '', role: str = '', status: str = '',
               department_id: int = 0, page: int = 1, per_page: int = 20):
    q = User.query
    if search:
        like = f'%{search}%'
        q = q.filter(
            (User.name.ilike(like)) | (User.email.ilike(like)) | (User.cpf.ilike(like))
        )
    if role:
        q = q.filter(User.role == role)
    if status:
        q = q.filter(User.status == status)
    if department_id:
        q = q.filter(User.department_id == department_id)
    return q.order_by(User.name).paginate(page=page, per_page=per_page, error_out=False)


# ─── Criar / Editar ───────────────────────────────────────────────────────────

def create_user(form, actor_id: int) -> User:
    dept_id = form.department_id.data or None

    # Verifica duplicidade antes de inserir
    email = form.email.data.strip().lower()
    cpf   = form.cpf.data  # já normalizado pelo validator
    if User.query.filter_by(email=email).first():
        raise ValueError('e-mail já cadastrado')
    if User.query.filter_by(cpf=cpf).first():
        raise ValueError('CPF já cadastrado')

    user = User(
        name          = form.name.data.strip(),
        cpf           = cpf,
        email         = email,
        role          = form.role.data,
        is_admin      = bool(form.is_admin.data),
        status        = form.status.data,
        department_id = dept_id,
        birth_date    = form.birth_date.data,
        first_login   = True,
    )
    # Senha temporária aleatória — o usuário a trocará no primeiro login
    user.set_password(secrets.token_urlsafe(24))

    if form.profile_picture.data:
        user.profile_picture = _save_profile_picture(form.profile_picture.data)

    try:
        db.session.add(user)
        db.session.flush()   # obtém user.id antes do commit
        _audit(actor_id, 'create', user.id,
               new={'name': user.name, 'email': user.email, 'role': user.role})
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise
    return user


def update_user(user: User, form, actor_id: int) -> User:
    old = {'name': user.name, 'cpf': user.cpf, 'email': user.email,
           'role': user.role, 'status': user.status}

    new_email = form.email.data.strip().lower()
    new_cpf   = form.cpf.data  # já normalizado pelo validator

    if new_email != user.email:
        conflict = User.query.filter(
            User.email == new_email, User.id != user.id
        ).first()
        if conflict:
            raise ValueError('e-mail já cadastrado')

    if new_cpf != user.cpf:
        conflict = User.query.filter(
            User.cpf == new_cpf, User.id != user.id
        ).first()
        if conflict:
            raise ValueError('CPF já cadastrado')

    user.name          = form.name.data.strip()
    user.cpf           = new_cpf
    user.email         = new_email
    user.role          = form.role.data
    user.is_admin      = bool(form.is_admin.data)
    user.status        = form.status.data
    user.department_id = form.department_id.data or None
    user.birth_date    = form.birth_date.data

    if form.profile_picture.data:
        user.profile_picture = _save_profile_picture(
            form.profile_picture.data, user.profile_picture
        )

    _audit(actor_id, 'update', user.id, old=old,
           new={'name': user.name, 'cpf': user.cpf, 'email': user.email,
                'role': user.role, 'status': user.status})
    db.session.commit()
    return user


# ─── Convite ─────────────────────────────────────────────────────────────────

def invite_user(form, actor_id: int) -> User:
    """Cria o usuário e envia e-mail de convite com link para definir senha."""
    from flask import url_for

    dept_id = form.department_id.data or None
    email   = form.email.data.strip().lower()
    cpf     = form.cpf.data  # já normalizado pelo validator

    if User.query.filter_by(email=email).first():
        raise ValueError('e-mail já cadastrado')
    if User.query.filter_by(cpf=cpf).first():
        raise ValueError('CPF já cadastrado')

    user = User(
        name          = form.name.data.strip(),
        cpf           = cpf,
        email         = email,
        role          = form.role.data,
        is_admin      = bool(form.is_admin.data),
        status        = 'active',
        department_id = dept_id,
        first_login   = True,
    )
    user.set_password(secrets.token_urlsafe(24))
    db.session.add(user)
    db.session.flush()

    raw_token = secrets.token_urlsafe(32)
    token = UserToken(
        user_id    = user.id,
        token      = raw_token,
        type       = 'invite',
        expires_at = datetime.utcnow() + timedelta(hours=48),
    )
    db.session.add(token)

    set_password_url = url_for('auth.reset_password', token=raw_token, _external=True)
    if not send_invite(user, set_password_url):
        db.session.rollback()
        raise RuntimeError('Não foi possível enviar o e-mail de convite. Verifique as configurações de SMTP.')

    _audit(actor_id, 'create', user.id,
           new={'name': user.name, 'email': user.email, 'via': 'invite'})
    db.session.commit()
    return user


# ─── Ações rápidas ────────────────────────────────────────────────────────────

def toggle_status(user: User, new_status: str, actor_id: int) -> None:
    old = user.status
    user.status = new_status
    if new_status == 'blocked':
        user.locked_until = None
        user.login_attempts = 0
    _audit(actor_id, 'update', user.id,
           old={'status': old}, new={'status': new_status})
    db.session.commit()


def reset_password_admin(user: User, actor_id: int) -> None:
    """Admin força reset: gera token e envia e-mail."""
    from app.services.auth_service import request_password_reset
    request_password_reset(user.email)
    _audit(actor_id, 'update', user.id, new={'action': 'admin_password_reset'})
    db.session.commit()


def unlock_user(user: User, actor_id: int) -> None:
    user.locked_until   = None
    user.login_attempts = 0
    _audit(actor_id, 'update', user.id, new={'action': 'unlocked'})
    db.session.commit()


# ─── Departamentos ────────────────────────────────────────────────────────────

def all_departments():
    return Department.query.order_by(Department.name).all()


def create_department(name: str, actor_id: int) -> Department:
    dept = Department(name=name.strip())
    db.session.add(dept)
    db.session.flush()
    _audit(actor_id, 'create', dept.id,
           new={'name': dept.name})
    db.session.commit()
    return dept


