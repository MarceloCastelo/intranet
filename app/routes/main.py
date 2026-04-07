from flask import Blueprint, render_template
from flask_login import login_required

from app.services.dashboard_service import get_dashboard_data

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
@login_required
def index():
    data = get_dashboard_data()
    return render_template('main/index.html', **data)
