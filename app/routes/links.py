from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app.forms.content import LinkForm
from app.services.content_service import (create_link, delete_link,
                                           get_link_or_404, list_links,
                                           update_link)
from app.utils.decorators import admin_required

links_bp = Blueprint('links', __name__, url_prefix='/admin/links')


@links_bp.route('/')
@login_required
@admin_required
def index():
    items = list_links()
    return render_template('links/index.html', links=items)


@links_bp.route('/criar', methods=['GET', 'POST'])
@login_required
@admin_required
def create():
    form = LinkForm()
    if form.validate_on_submit():
        create_link(form, actor_id=current_user.id)
        flash('Link criado.', 'success')
        return redirect(url_for('links.index'))
    return render_template('links/form.html', form=form, title='Novo link', link=None)


@links_bp.route('/<int:link_id>/editar', methods=['GET', 'POST'])
@login_required
@admin_required
def edit(link_id):
    link = get_link_or_404(link_id)
    form = LinkForm(obj=link)
    if form.validate_on_submit():
        update_link(link, form)
        flash('Link atualizado.', 'success')
        return redirect(url_for('links.index'))
    return render_template('links/form.html', form=form, title='Editar link', link=link)


@links_bp.route('/<int:link_id>/excluir', methods=['POST'])
@login_required
@admin_required
def delete(link_id):
    link = get_link_or_404(link_id)
    delete_link(link)
    flash('Link excluído.', 'success')
    return redirect(url_for('links.index'))
