from datetime import datetime

from flask import Blueprint, abort, current_app, flash, jsonify, redirect, render_template, request, session, url_for
from flask_login import current_user, login_required

from app import db
from app.models.user import Department, Session as DbSession, User
from app.models.content import SiteConfig
from app.services.content_service import active_banners
from app.services.dashboard_service import get_dashboard_data

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def index():
    """Landing pública: seleção de portal."""
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    return render_template('main/landing.html')


@main_bp.route('/home')
@login_required
def home():
    data = get_dashboard_data()
    data['banners'] = active_banners()
    return render_template('main/index.html', **data)


@main_bp.route('/colaboradores')
@login_required
def directory():
    if not current_user.is_admin:
        abort(403)
    search = request.args.get('q', '').strip()
    department_id = request.args.get('department_id', 0, type=int)

    q = User.query.filter_by(status='active')
    if search:
        like = f'%{search}%'
        q = q.filter((User.name.ilike(like)) | (User.email.ilike(like)))
    if department_id:
        q = q.filter(User.department_id == department_id)

    users = q.order_by(User.name).all()
    departments = Department.query.order_by(Department.name).all()
    return render_template('main/directory.html',
                           users=users,
                           departments=departments,
                           search=search,
                           department_id=department_id)


# ─── Heartbeat ───────────────────────────────────────────────────────────────

@main_bp.route('/api/heartbeat')
@login_required
def heartbeat():
    """Atualiza last_seen_at da sessão ativa (chamado pelo JS a cada 60s)."""
    db_session_id = session.get('db_session_id')
    if db_session_id:
        db_sess = db.session.get(DbSession, db_session_id)
        if db_sess and db_sess.user_id == current_user.id:
            db_sess.last_seen_at = datetime.utcnow()
            db.session.commit()
    return jsonify({'ok': True})


# ─── Power BI ─────────────────────────────────────────────────────────────────

def _can_access_powerbi():
    return current_user.is_admin or current_user.power_bi_access


@main_bp.route('/powerbi')
@login_required
def powerbi():
    if not _can_access_powerbi():
        abort(403)
    current_url = SiteConfig.get('power_bi_url') or current_app.config.get('POWER_BI_URL', '')
    return render_template('main/powerbi.html', current_url=current_url)


@main_bp.route('/powerbi/embed-url')
@login_required
def powerbi_embed_url():
    """Retorna a URL do relatório apenas para usuários autorizados.
    A URL nunca é exposta diretamente no HTML."""
    if not _can_access_powerbi():
        abort(403)
    url = SiteConfig.get('power_bi_url') or current_app.config.get('POWER_BI_URL', '')
    if not url:
        abort(404)
    return jsonify({'url': url})


@main_bp.route('/powerbi/update-url', methods=['POST'])
@login_required
def powerbi_update_url():
    """Permite que admins atualizem a URL do Power BI."""
    if not current_user.is_admin:
        abort(403)
    url = request.form.get('url', '').strip()
    SiteConfig.set('power_bi_url', url)
    db.session.commit()
    flash('URL do Power BI atualizada com sucesso.', 'success')
    return redirect(url_for('main.powerbi'))


# ─── Páginas estáticas públicas ───────────────────────────────────────────────

@main_bp.route('/termos-de-uso')
def terms():
    content_json = SiteConfig.get('terms_content', '')
    page_title   = SiteConfig.get('terms_title', 'Termos de Uso')
    return render_template('main/terms.html', content_json=content_json, page_title=page_title)


@main_bp.route('/politica-de-privacidade')
def privacy():
    content_json = SiteConfig.get('privacy_content', '')
    return render_template('main/privacy.html', content_json=content_json)


# ─── Administração — Página Inicial ──────────────────────────────────────────

@main_bp.route('/admin/pagina-inicial/termos', methods=['GET', 'POST'])
@login_required
def admin_terms():
    if not current_user.is_admin:
        abort(403)
    if request.method == 'POST':
        SiteConfig.set('terms_content', request.form.get('content_json', ''))
        new_title = request.form.get('page_title', '').strip()
        if new_title:
            SiteConfig.set('terms_title', new_title)
        db.session.commit()
        flash('Termos de Uso atualizados com sucesso.', 'success')
        return redirect(url_for('main.admin_terms'))
    content_json = SiteConfig.get('terms_content', '')
    page_title   = SiteConfig.get('terms_title', 'Termos de Uso')
    return render_template('main/admin/static_page_edit.html',
                           title='Termos de Uso',
                           page_key='terms',
                           page_title=page_title,
                           content_json=content_json)


@main_bp.route('/admin/pagina-inicial/privacidade', methods=['GET', 'POST'])
@login_required
def admin_privacy():
    if not current_user.is_admin:
        abort(403)
    if request.method == 'POST':
        SiteConfig.set('privacy_content', request.form.get('content_json', ''))
        db.session.commit()
        flash('Política de Privacidade atualizada com sucesso.', 'success')
        return redirect(url_for('main.admin_privacy'))
    content_json = SiteConfig.get('privacy_content', '')
    return render_template('main/admin/static_page_edit.html',
                           title='Política de Privacidade',
                           page_key='privacy',
                           content_json=content_json)
