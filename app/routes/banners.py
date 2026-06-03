from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app.forms.content import BannerForm
from app.services.content_service import (create_banner, delete_banner,
                                           get_banner_or_404, list_banners,
                                           update_banner)
from app.utils.decorators import editor_or_admin_required

banners_bp = Blueprint('banners', __name__, url_prefix='/admin/banners')


@banners_bp.route('/')
@login_required
@editor_or_admin_required
def index():
    items = list_banners()
    return render_template('banners/index.html', banners=items)


@banners_bp.route('/criar', methods=['GET', 'POST'])
@login_required
@editor_or_admin_required
def create():
    form = BannerForm()
    if form.validate_on_submit():
        if not form.image.data or not form.image.data.filename:
            form.image.errors.append('A imagem é obrigatória.')
        else:
            banner = create_banner(form, actor_id=current_user.id)
            flash('Banner criado.', 'success')
            return redirect(url_for('banners.index'))
    return render_template('banners/form.html', form=form, title='Novo banner', banner=None)


@banners_bp.route('/<int:banner_id>/editar', methods=['GET', 'POST'])
@login_required
@editor_or_admin_required
def edit(banner_id):
    banner = get_banner_or_404(banner_id)
    form = BannerForm(obj=banner)
    if form.validate_on_submit():
        update_banner(banner, form)
        flash('Banner atualizado.', 'success')
        return redirect(url_for('banners.index'))
    return render_template('banners/form.html', form=form, title='Editar banner', banner=banner)


@banners_bp.route('/<int:banner_id>/excluir', methods=['POST'])
@login_required
@editor_or_admin_required
def delete(banner_id):
    banner = get_banner_or_404(banner_id)
    delete_banner(banner)
    flash('Banner excluído.', 'success')
    return redirect(url_for('banners.index'))
