from functools import wraps

from flask import abort
from flask_login import current_user


def role_required(*roles):
    """Restringe acesso a determinados perfis. Ex: @role_required('admin')"""
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if not current_user.is_authenticated:
                abort(401)
            if current_user.role not in roles:
                abort(403)
            return f(*args, **kwargs)
        return decorated
    return decorator


def admin_required(f):
    return role_required('admin')(f)


def editor_or_admin_required(f):
    return role_required('admin', 'editor')(f)
