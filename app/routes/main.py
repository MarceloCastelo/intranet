from flask import Blueprint, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app.models.user import Department, User
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
