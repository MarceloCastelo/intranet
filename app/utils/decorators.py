from functools import wraps

from flask import abort
from flask_login import current_user

# Rótulos de exibição por role
ROLE_LABELS = {
    'user':          'Usuário',
    'editor':        'Editor',
    'rh':            'RH',
    'patrimonio':    'Patrimônio',
    'controladoria': 'Controladoria',
}


def admin_required(f):
    """Exige que o usuário tenha is_admin=True."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated:
            abort(401)
        if not current_user.is_admin:
            abort(403)
        return f(*args, **kwargs)
    return decorated


def editor_or_admin_required(f):
    """Editor ou qualquer perfil com is_admin=True."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated:
            abort(401)
        if not (current_user.role == 'editor' or current_user.is_admin):
            abort(403)
        return f(*args, **kwargs)
    return decorated


def ouvidoria_required(f):
    """Acesso ao painel de ouvidoria: apenas roles rh/patrimonio/controladoria."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated:
            abort(401)
        if current_user.role not in ('rh', 'patrimonio', 'controladoria'):
            abort(403)
        return f(*args, **kwargs)
    return decorated
