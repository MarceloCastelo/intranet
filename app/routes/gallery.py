from flask import (Blueprint, flash, redirect, render_template, request,
                   url_for)
from flask_login import current_user, login_required

from app.forms.gallery import GalleryForm
from app.services.gallery_service import (add_items, create_gallery,
                                           delete_gallery, delete_item,
                                           get_gallery_or_404, get_item_or_404,
                                           list_galleries, set_cover,
                                           update_gallery)
from app.utils.decorators import admin_required, editor_or_admin_required

gallery_bp = Blueprint('gallery', __name__, url_prefix='/galeria')


@gallery_bp.route('/')
@login_required
def index():
    page       = request.args.get('page', 1, type=int)
    pagination = list_galleries(page=page)
    return render_template('gallery/index.html', pagination=pagination)


@gallery_bp.route('/admin/criar', methods=['GET', 'POST'])
@login_required
@editor_or_admin_required
def create():
    form = GalleryForm()
    if form.validate_on_submit():
        gallery = create_gallery(form, actor_id=current_user.id)
        flash('Galeria criada. Agora adicione as imagens.', 'success')
        return redirect(url_for('gallery.upload', gallery_id=gallery.id))
    return render_template('gallery/form.html', form=form, title='Nova galeria', gallery=None)


@gallery_bp.route('/admin/<int:gallery_id>/editar', methods=['GET', 'POST'])
@login_required
@editor_or_admin_required
def edit(gallery_id):
    gallery = get_gallery_or_404(gallery_id)
    form    = GalleryForm(obj=gallery)
    if form.validate_on_submit():
        update_gallery(gallery, form)
        flash('Galeria atualizada.', 'success')
        return redirect(url_for('gallery.detail', gallery_id=gallery.id))
    return render_template('gallery/form.html', form=form, title='Editar galeria', gallery=gallery)


@gallery_bp.route('/admin/<int:gallery_id>/excluir', methods=['POST'])
@login_required
@admin_required
def delete(gallery_id):
    gallery = get_gallery_or_404(gallery_id)
    delete_gallery(gallery)
    flash('Galeria excluída.', 'success')
    return redirect(url_for('gallery.index'))


@gallery_bp.route('/<int:gallery_id>')
@login_required
def detail(gallery_id):
    from app.services.interaction_service import interaction_context
    gallery = get_gallery_or_404(gallery_id)
    items   = sorted(gallery.items, key=lambda i: i.order_position)
    ctx = interaction_context('gallery', gallery.id, current_user.id)
    return render_template('gallery/detail.html', gallery=gallery, items=items, **ctx)


# ─── Upload de imagens ────────────────────────────────────────────────────────

@gallery_bp.route('/admin/<int:gallery_id>/upload', methods=['GET', 'POST'])
@login_required
@editor_or_admin_required
def upload(gallery_id):
    gallery = get_gallery_or_404(gallery_id)
    if request.method == 'POST':
        files    = request.files.getlist('images')
        captions = request.form.getlist('caption')
        if not files or all(not f.filename for f in files):
            flash('Selecione ao menos uma imagem.', 'warning')
        else:
            add_items(gallery, files, captions, actor_id=current_user.id)
            flash(f'{sum(1 for f in files if f.filename)} imagem(ns) adicionada(s).', 'success')
            return redirect(url_for('gallery.detail', gallery_id=gallery.id))
    return render_template('gallery/upload.html', gallery=gallery)


# ─── Ações por item ───────────────────────────────────────────────────────────

@gallery_bp.route('/admin/item/<int:item_id>/excluir', methods=['POST'])
@login_required
@editor_or_admin_required
def delete_item_view(item_id):
    item       = get_item_or_404(item_id)
    gallery_id = item.gallery_id
    delete_item(item)
    flash('Imagem removida.', 'success')
    return redirect(url_for('gallery.detail', gallery_id=gallery_id))


@gallery_bp.route('/admin/item/<int:item_id>/capa', methods=['POST'])
@login_required
@editor_or_admin_required
def set_cover_view(item_id):
    item    = get_item_or_404(item_id)
    gallery = item.gallery
    set_cover(gallery, item)
    flash('Capa atualizada.', 'success')
    return redirect(url_for('gallery.detail', gallery_id=gallery.id))
