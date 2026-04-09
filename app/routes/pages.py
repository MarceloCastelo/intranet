from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app.forms.pages import PageForm
from app.services.page_service import (all_published_pages, create_page,
                                        delete_page, get_page_by_slug,
                                        get_page_or_404, list_pages,
                                        tiptap_to_html, update_page)
from app.routes.approvals import request_approval
from app.utils.decorators import editor_or_admin_required

pages_bp = Blueprint('pages', __name__, url_prefix='/paginas')


# ─── Lista pública ────────────────────────────────────────────────────────────

@pages_bp.route('/')
@login_required
def public_list():
    pages = all_published_pages()
    return render_template('pages/public_list.html', pages=pages)


# ─── Visualização pública ─────────────────────────────────────────────────────

@pages_bp.route('/<slug>')
@login_required
def view(slug: str):
    page = get_page_by_slug(slug)
    if not page:
        abort(404)
    content_html = tiptap_to_html(page.content_json)
    return render_template('pages/view.html', page=page, content_html=content_html)


# ─── Admin: lista ─────────────────────────────────────────────────────────────

@pages_bp.route('/admin')
@login_required
@editor_or_admin_required
def index():
    search     = request.args.get('q', '').strip()
    page_num   = request.args.get('page', 1, type=int)
    pagination = list_pages(page=page_num, search=search)
    return render_template('pages/index.html', pagination=pagination, search=search)


# ─── Admin: criar ─────────────────────────────────────────────────────────────

@pages_bp.route('/admin/criar', methods=['GET', 'POST'])
@login_required
@editor_or_admin_required
def create():
    form = PageForm()
    if form.validate_on_submit():
        page = create_page(form, actor_id=current_user.id, force_draft=not current_user.is_admin)
        if not current_user.is_admin and form.is_published.data:
            request_approval('publish', 'page', page.id, page.name,
                             requested_by_id=current_user.id)
            flash(f'Página "{page.name}" criada. Solicitação de publicação enviada para aprovação.', 'info')
        else:
            flash(f'Página "{page.name}" criada com sucesso.', 'success')
        return redirect(url_for('pages.detail', page_id=page.id))
    return render_template('pages/form.html', form=form, title='Nova página', page=None)


# ─── Admin: detalhe ───────────────────────────────────────────────────────────

@pages_bp.route('/admin/<int:page_id>')
@login_required
@editor_or_admin_required
def detail(page_id: int):
    page = get_page_or_404(page_id)
    return render_template('pages/detail.html', page=page)


# ─── Admin: editar ────────────────────────────────────────────────────────────

@pages_bp.route('/admin/<int:page_id>/editar', methods=['GET', 'POST'])
@login_required
@editor_or_admin_required
def edit(page_id: int):
    page = get_page_or_404(page_id)
    form = PageForm(obj=page)

    if request.method == 'GET':
        import json
        form.content_json.data = json.dumps(page.content_json)

    if form.validate_on_submit():
        if not current_user.is_admin and page.is_published:
            import json
            snapshot = {
                'name':         form.name.data.strip(),
                'slug':         form.slug.data.strip() if hasattr(form, 'slug') and form.slug.data else None,
                'content_json': json.loads(form.content_json.data),
            }
            request_approval('edit', 'page', page.id, page.name,
                             requested_by_id=current_user.id, snapshot=snapshot)
            flash('Edição enviada para aprovação do administrador.', 'info')
            return redirect(url_for('pages.detail', page_id=page.id))
        update_page(page, form, actor_id=current_user.id)
        flash('Página atualizada.', 'success')
        return redirect(url_for('pages.detail', page_id=page.id))

    return render_template('pages/form.html', form=form,
                           title=f'Editar — {page.name}', page=page)


# ─── Admin: excluir ───────────────────────────────────────────────────────────

@pages_bp.route('/admin/<int:page_id>/excluir', methods=['POST'])
@login_required
@editor_or_admin_required
def delete(page_id: int):
    page = get_page_or_404(page_id)
    if not current_user.is_admin:
        request_approval('delete', 'page', page.id, page.name,
                        requested_by_id=current_user.id)
        flash('Solicitação de exclusão enviada para aprovação do administrador.', 'info')
        return redirect(url_for('pages.detail', page_id=page.id))
    name = page.name
    delete_page(page, actor_id=current_user.id)
    flash(f'Página "{name}" excluída.', 'success')
    return redirect(url_for('pages.index'))


# ─── Admin: publicar/despublicar ─────────────────────────────────────────────

@pages_bp.route('/admin/<int:page_id>/publicar', methods=['POST'])
@login_required
@editor_or_admin_required
def toggle_publish(page_id: int):
    page = get_page_or_404(page_id)
    if not current_user.is_admin:
        action = 'unpublish' if page.is_published else 'publish'
        request_approval(action, 'page', page.id, page.name,
                        requested_by_id=current_user.id)
        msg = 'Solicitação de despublicação enviada para aprovação.' if page.is_published \
              else 'Solicitação de publicação enviada para aprovação.'
        flash(msg, 'info')
        return redirect(url_for('pages.detail', page_id=page.id))
    page.is_published = not page.is_published
    from app import db
    db.session.commit()
    status = 'publicada' if page.is_published else 'despublicada'
    flash(f'Página {status}.', 'success')
    return redirect(url_for('pages.detail', page_id=page.id))
