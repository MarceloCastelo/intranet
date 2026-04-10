from flask import Blueprint, flash, redirect, render_template, url_for
from flask_login import current_user, login_required

from app.forms.services import ServiceForm
from app.routes.approvals import request_approval
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
        svc = create_service(form, actor_id=current_user.id, force_inactive=not current_user.is_admin)
        if not current_user.is_admin:
            request_approval('publish', 'service', svc.id, svc.title,
                             requested_by_id=current_user.id)
            flash('Serviço cadastrado. Solicitação enviada para aprovação do administrador.', 'info')
        else:
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
        if not current_user.is_admin and svc.is_active:
            snapshot = {
                'title':       form.title.data.strip(),
                'url':         form.url.data.strip(),
                'description': form.description.data.strip() if form.description.data else None,
                'category':    form.category.data,
            }
            request_approval('edit', 'service', svc.id, svc.title,
                             requested_by_id=current_user.id, snapshot=snapshot)
            flash('Edição enviada para aprovação do administrador.', 'info')
            return redirect(url_for('services.admin'))
        update_service(svc, form)
        flash('Serviço atualizado.', 'success')
        return redirect(url_for('services.admin'))
    return render_template('services/form.html', form=form, title='Editar serviço', svc=svc)


@services_bp.route('/admin/<int:svc_id>/excluir', methods=['POST'])
@login_required
@editor_or_admin_required
def delete(svc_id):
    svc = get_service_or_404(svc_id)
    if not current_user.is_admin:
        request_approval('delete', 'service', svc.id, svc.title,
                         requested_by_id=current_user.id)
        flash('Solicitação de exclusão enviada para aprovação do administrador.', 'info')
        return redirect(url_for('services.admin'))
    delete_service(svc)
    flash('Serviço excluído.', 'success')
    return redirect(url_for('services.admin'))
