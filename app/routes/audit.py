from flask import Blueprint, render_template, request
from flask_login import login_required

from app.models.audit import AuditLog
from app.models.user import User
from app.utils.decorators import admin_required

audit_bp = Blueprint('audit', __name__, url_prefix='/admin/auditoria')

# Mapeamento de labels para exibição
ACTION_LABELS = {
    'create':  ('Criação',     'bg-green-100 text-green-700'),
    'update':  ('Edição',      'bg-blue-100 text-blue-700'),
    'delete':  ('Exclusão',    'bg-red-100 text-red-700'),
    'publish': ('Publicação',  'bg-purple-100 text-purple-700'),
    'approve': ('Aprovação',   'bg-yellow-100 text-yellow-700'),
    'login':   ('Login',       'bg-gray-100 text-gray-700'),
    'logout':  ('Logout',      'bg-gray-100 text-gray-600'),
    'invite':  ('Convite',     'bg-indigo-100 text-indigo-700'),
    'block':   ('Bloqueio',    'bg-red-100 text-red-700'),
    'unblock': ('Desbloqueio', 'bg-green-100 text-green-700'),
    'reset_password': ('Reset de senha', 'bg-orange-100 text-orange-700'),
}

ENTITY_LABELS = {
    'news':    'Notícia',
    'event':   'Evento',
    'user':    'Usuário',
    'banner':  'Banner',
    'gallery': 'Galeria',
    'faq':     'FAQ',
    'poll':    'Enquete',
    'service': 'Serviço',
    'comment': 'Comentário',
}


@audit_bp.route('/')
@login_required
@admin_required
def index():
    page       = request.args.get('page', 1, type=int)
    action_f   = request.args.get('action', '').strip()
    entity_f   = request.args.get('entity', '').strip()
    user_id_f  = request.args.get('user_id', 0, type=int)

    q = AuditLog.query.order_by(AuditLog.created_at.desc())

    if action_f:
        q = q.filter(AuditLog.action == action_f)
    if entity_f:
        q = q.filter(AuditLog.entity == entity_f)
    if user_id_f:
        q = q.filter(AuditLog.user_id == user_id_f)

    pagination = q.paginate(page=page, per_page=50, error_out=False)
    users      = User.query.order_by(User.name).all()

    return render_template(
        'audit/index.html',
        pagination=pagination,
        action_f=action_f,
        entity_f=entity_f,
        user_id_f=user_id_f,
        users=users,
        action_labels=ACTION_LABELS,
        entity_labels=ENTITY_LABELS,
    )
