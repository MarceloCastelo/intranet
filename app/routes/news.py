from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app.forms.news import CategoryForm, NewsForm
from app.services.news_service import (all_categories, create_category,
                                        create_news, delete_news,
                                        get_news_or_404, list_news,
                                        record_view, toggle_publish,
                                        update_news)
from app.utils.decorators import editor_or_admin_required

news_bp = Blueprint('news', __name__, url_prefix='/noticias')


def _populate_categories(form):
    cats = all_categories()
    form.categories.choices = [(c.id, c.name) for c in cats]
    return cats


# ── Lista (admin/editor) ──────────────────────────────────────────────────────

@news_bp.route('/admin')
@login_required
@editor_or_admin_required
def index():
    search      = request.args.get('q', '').strip()
    category_id = request.args.get('category_id', 0, type=int)
    published   = request.args.get('published', '')
    page        = request.args.get('page', 1, type=int)
    pagination  = list_news(search=search, category_id=category_id,
                             published=published, page=page)
    categories  = all_categories()
    return render_template('news/index.html',
                           pagination=pagination,
                           search=search,
                           category_id=category_id,
                           published=published,
                           categories=categories)


# ── Criar ─────────────────────────────────────────────────────────────────────

@news_bp.route('/admin/criar', methods=['GET', 'POST'])
@login_required
@editor_or_admin_required
def create():
    form = NewsForm()
    cats = _populate_categories(form)
    if form.validate_on_submit():
        news = create_news(form, author_id=current_user.id)
        flash('Notícia criada com sucesso.', 'success')
        return redirect(url_for('news.detail_admin', news_id=news.id))
    return render_template('news/form.html', form=form, title='Nova notícia',
                           categories=cats, news=None)


# ── Editar ────────────────────────────────────────────────────────────────────

@news_bp.route('/admin/<int:news_id>/editar', methods=['GET', 'POST'])
@login_required
@editor_or_admin_required
def edit(news_id):
    news = get_news_or_404(news_id)
    form = NewsForm(obj=news)
    cats = _populate_categories(form)

    if request.method == 'GET':
        form.categories.data  = [c.id for c in news.categories]
        form.tags_input.data  = ', '.join(t.name for t in news.tags)
        import json
        form.content_json.data = json.dumps(news.content_json)

    if form.validate_on_submit():
        update_news(news, form, actor_id=current_user.id)
        flash('Notícia atualizada.', 'success')
        return redirect(url_for('news.detail_admin', news_id=news.id))

    return render_template('news/form.html', form=form, title='Editar notícia',
                           categories=cats, news=news)


# ── Detalhe (painel) ──────────────────────────────────────────────────────────

@news_bp.route('/admin/<int:news_id>')
@login_required
@editor_or_admin_required
def detail_admin(news_id):
    news = get_news_or_404(news_id)
    return render_template('news/detail_admin.html', news=news)


# ── Publicar / despublicar ────────────────────────────────────────────────────

@news_bp.route('/admin/<int:news_id>/publicar', methods=['POST'])
@login_required
@editor_or_admin_required
def publish(news_id):
    news = get_news_or_404(news_id)
    toggle_publish(news, actor_id=current_user.id)
    status = 'publicada' if news.is_published else 'despublicada'
    flash(f'Notícia {status}.', 'success')
    return redirect(url_for('news.detail_admin', news_id=news.id))


# ── Excluir ───────────────────────────────────────────────────────────────────

@news_bp.route('/admin/<int:news_id>/excluir', methods=['POST'])
@login_required
@editor_or_admin_required
def delete(news_id):
    news = get_news_or_404(news_id)
    delete_news(news, actor_id=current_user.id)
    flash('Notícia excluída.', 'success')
    return redirect(url_for('news.index'))


# ── Categorias ────────────────────────────────────────────────────────────────

@news_bp.route('/admin/categorias', methods=['GET', 'POST'])
@login_required
@editor_or_admin_required
def categories():
    form = CategoryForm()
    if form.validate_on_submit():
        create_category(form)
        flash('Categoria criada.', 'success')
        return redirect(url_for('news.categories'))
    cats = all_categories()
    return render_template('news/categories.html', form=form, categories=cats)


# ── Leitura pública ───────────────────────────────────────────────────────────

@news_bp.route('/')
@login_required
def public_list():
    from app.models.news import News
    search      = request.args.get('q', '').strip()
    category_id = request.args.get('category_id', 0, type=int)
    page        = request.args.get('page', 1, type=int)
    q = News.query.filter_by(is_published=True)
    if search:
        like = f'%{search}%'
        q = q.filter(News.title.ilike(like) | News.summary.ilike(like))
    if category_id:
        q = q.filter(News.categories.any(id=category_id))
    pagination = q.order_by(News.published_at.desc()).paginate(page=page, per_page=12, error_out=False)
    categories = all_categories()
    return render_template('news/public_list.html',
                           pagination=pagination, search=search,
                           category_id=category_id, categories=categories)


@news_bp.route('/<slug>')
@login_required
def view(slug):
    from app.models.news import News
    from app.services.interaction_service import interaction_context
    news = News.query.filter_by(slug=slug, is_published=True).first_or_404()
    ip = request.headers.get('X-Forwarded-For', request.remote_addr or '').split(',')[0].strip()
    record_view(news, user_id=current_user.id, ip=ip)
    ctx = interaction_context('news', news.id, current_user.id)
    return render_template('news/view.html', news=news, **ctx)
