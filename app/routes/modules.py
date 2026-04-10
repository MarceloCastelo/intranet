from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import login_required

from app import db
from app.models.content import SiteModule
from app.utils.decorators import admin_required

modules_bp = Blueprint('modules', __name__, url_prefix='/admin/modulos')

# Módulos padrão (chave → nome de exibição)
_DEFAULT_MODULES = [
    ('news',       'Notícias'),
    ('events',     'Eventos'),
    ('faq',        'FAQ'),
    ('polls',      'Enquetes'),
    ('gallery',    'Galeria'),
    ('extensions', 'Ramais'),
    ('services',   'Serviços'),
    ('directory',  'Colaboradores'),
    ('pages',      'Páginas'),
    ('links',      'Links'),
]


@modules_bp.route('/')
@login_required
@admin_required
def index():
    # Garante que todos os módulos padrão existam na tabela
    _seed_modules()
    modules = SiteModule.query.order_by(SiteModule.name).all()
    return render_template('modules/index.html', modules=modules)


@modules_bp.route('/<key>/toggle', methods=['POST'])
@login_required
@admin_required
def toggle(key: str):
    mod = db.session.get(SiteModule, key) or abort(404)
    mod.is_active = not mod.is_active
    db.session.commit()
    status = 'ativado' if mod.is_active else 'desativado'
    flash(f'Módulo "{mod.name}" {status} com sucesso.', 'success')
    return redirect(url_for('modules.index'))


def _seed_modules():
    """Insere módulos padrão que ainda não existam no banco."""
    for key, name in _DEFAULT_MODULES:
        if not db.session.get(SiteModule, key):
            db.session.add(SiteModule(key=key, name=name, is_active=True))
    db.session.commit()
