from datetime import datetime

from flask import Blueprint, abort, jsonify, redirect, render_template, request, session, url_for
from flask_login import current_user, login_required

from app import db
from app.models.user import Department, Session as DbSession, User
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
