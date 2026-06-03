from flask import Blueprint, flash, redirect, render_template, url_for
from flask_login import current_user, login_required

from app.forms.services import ServiceForm
from app.services.service_srv import (create_service, delete_service,
                                       get_service_or_404, list_all_services,
                                       list_services_grouped, update_service)
from app.utils.decorators import admin_required, editor_or_admin_required

services_bp = Blueprint('services', __name__, url_prefix='/servicos')


@services_bp.route('/')
@login_required
def index():
    grouped = list_services_grouped(active_only=True)
    return render_template('services/index.html', grouped=grouped)


@services_bp.route('/admin')
@login_required
@editor_or_admin_required
def admin():
    all_svcs = list_all_services()
    return render_template('services/admin.html', services=all_svcs)


@services_bp.route('/admin/criar', methods=['GET', 'POST'])
@login_required
@editor_or_admin_required
def create():
    form = ServiceForm()
    if form.validate_on_submit():
        svc = create_service(form, actor_id=current_user.id)
        flash('Serviço cadastrado.', 'success')
        return redirect(url_for('services.admin'))
    return render_template('services/form.html', form=form, title='Novo serviço', svc=None)


@services_bp.route('/admin/<int:svc_id>/editar', methods=['GET', 'POST'])
@login_required
@editor_or_admin_required
def edit(svc_id):
    svc  = get_service_or_404(svc_id)
    form = ServiceForm(obj=svc)
    if form.validate_on_submit():
        update_service(svc, form)
        flash('Serviço atualizado.', 'success')
        return redirect(url_for('services.admin'))
    return render_template('services/form.html', form=form, title='Editar serviço', svc=svc)


@services_bp.route('/admin/<int:svc_id>/excluir', methods=['POST'])
@login_required
@editor_or_admin_required
def delete(svc_id):
    svc = get_service_or_404(svc_id)
    delete_service(svc)
    flash('Serviço excluído.', 'success')
    return redirect(url_for('services.admin'))
