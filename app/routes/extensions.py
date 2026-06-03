from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app.forms.extensions import PhoneExtensionForm
from app.services.extension_service import (create_extension, delete_extension,
                                              get_extension_or_404,
                                              list_extensions, set_form_choices,
                                              update_extension)
from app.utils.decorators import editor_or_admin_required

extensions_bp = Blueprint('extensions', __name__, url_prefix='/ramais')


@extensions_bp.route('/')
@login_required
def index():
    search = request.args.get('q', '').strip()
    exts   = list_extensions(search=search, active_only=True)

    grouped = {}
    for ext in exts:
        dept_name = ext.department.name if ext.department else 'Sem departamento'
        grouped.setdefault(dept_name, []).append(ext)

    return render_template('extensions/index.html',
                           grouped=grouped, search=search, total=len(exts))


@extensions_bp.route('/admin')
@login_required
@editor_or_admin_required
def admin_index():
    search = request.args.get('q', '').strip()
    exts   = list_extensions(search=search, active_only=False)

    grouped = {}
    for ext in exts:
        dept_name = ext.department.name if ext.department else 'Sem departamento'
        grouped.setdefault(dept_name, []).append(ext)

    return render_template('extensions/index.html',
                           grouped=grouped, search=search, total=len(exts))


@extensions_bp.route('/admin/criar', methods=['GET', 'POST'])
@login_required
@editor_or_admin_required
def create():
    form = PhoneExtensionForm()
    set_form_choices(form)
    if form.validate_on_submit():
        ext = create_extension(form, actor_id=current_user.id)
        flash('Ramal cadastrado.', 'success')
        return redirect(url_for('extensions.admin_index'))
    return render_template('extensions/form.html', form=form,
                           title='Novo ramal', ext=None)


@extensions_bp.route('/admin/<int:ext_id>/editar', methods=['GET', 'POST'])
@login_required
@editor_or_admin_required
def edit(ext_id):
    ext  = get_extension_or_404(ext_id)
    form = PhoneExtensionForm(obj=ext)
    set_form_choices(form)
    if form.validate_on_submit():
        update_extension(ext, form)
        flash('Ramal atualizado.', 'success')
        return redirect(url_for('extensions.admin_index'))
    return render_template('extensions/form.html', form=form,
                           title='Editar ramal', ext=ext)


@extensions_bp.route('/admin/<int:ext_id>/excluir', methods=['POST'])
@login_required
@editor_or_admin_required
def delete(ext_id):
    ext = get_extension_or_404(ext_id)
    delete_extension(ext)
    flash('Ramal excluído.', 'success')
    return redirect(url_for('extensions.admin_index'))
