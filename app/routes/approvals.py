from datetime import datetime

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app import db
from app.models.approval import ContentApproval
from app.utils.decorators import admin_required

approvals_bp = Blueprint('approvals', __name__, url_prefix='/admin/aprovacoes')

# ─── Labels de exibição ───────────────────────────────────────────────────────

ACTION_LABELS = {
    'publish':   ('Publicar',     'bg-green-100 text-green-700'),
    'unpublish': ('Despublicar',  'bg-yellow-100 text-yellow-700'),
    'edit':      ('Editar',       'bg-blue-100 text-blue-700'),
    'delete':    ('Excluir',      'bg-red-100 text-red-700'),
}

STATUS_LABELS = {
    'pending':  ('Pendente',  'bg-yellow-100 text-yellow-700'),
    'approved': ('Aprovado',  'bg-green-100 text-green-700'),
    'rejected': ('Rejeitado', 'bg-red-100 text-red-700'),
}

TYPE_LABELS = {
    'news': 'Notícia',
    'page': 'Página',
}

# ─── Lista de aprovações ──────────────────────────────────────────────────────

@approvals_bp.route('/')
@login_required
@admin_required
def index():
    status_f = request.args.get('status', 'pending')
    page     = request.args.get('page', 1, type=int)

    q = ContentApproval.query.order_by(ContentApproval.requested_at.desc())
    if status_f in ('pending', 'approved', 'rejected'):
        q = q.filter(ContentApproval.status == status_f)

    pagination = q.paginate(page=page, per_page=30, error_out=False)
    pending_count = ContentApproval.query.filter_by(status='pending').count()

    return render_template(
        'approvals/index.html',
        pagination=pagination,
        status_f=status_f,
        action_labels=ACTION_LABELS,
        status_labels=STATUS_LABELS,
        type_labels=TYPE_LABELS,
        pending_count=pending_count,
    )


# ─── Aprovar ──────────────────────────────────────────────────────────────────

@approvals_bp.route('/<int:approval_id>/aprovar', methods=['POST'])
@login_required
@admin_required
def approve(approval_id: int):
    approval = db.session.get(ContentApproval, approval_id) or abort(404)
    if approval.status != 'pending':
        flash('Esta solicitação já foi processada.', 'warning')
        return redirect(url_for('approvals.index'))

    note = request.form.get('note', '').strip()

    try:
        _execute_action(approval)
    except Exception as exc:
        flash(f'Erro ao executar a ação: {exc}', 'danger')
        return redirect(url_for('approvals.index'))

    approval.status        = 'approved'
    approval.reviewed_by_id = current_user.id
    approval.reviewed_at   = datetime.utcnow()
    approval.review_note   = note or None
    db.session.commit()

    flash('Solicitação aprovada e ação executada.', 'success')
    return redirect(url_for('approvals.index'))


# ─── Rejeitar ─────────────────────────────────────────────────────────────────

@approvals_bp.route('/<int:approval_id>/rejeitar', methods=['POST'])
@login_required
@admin_required
def reject(approval_id: int):
    approval = db.session.get(ContentApproval, approval_id) or abort(404)
    if approval.status != 'pending':
        flash('Esta solicitação já foi processada.', 'warning')
        return redirect(url_for('approvals.index'))

    note = request.form.get('note', '').strip()
    if not note:
        flash('Informe o motivo da rejeição.', 'warning')
        return redirect(url_for('approvals.index'))

    approval.status         = 'rejected'
    approval.reviewed_by_id = current_user.id
    approval.reviewed_at    = datetime.utcnow()
    approval.review_note    = note
    db.session.commit()

    flash('Solicitação rejeitada.', 'info')
    return redirect(url_for('approvals.index'))


# ─── Execução da ação após aprovação ─────────────────────────────────────────

def _execute_action(approval: ContentApproval) -> None:
    """Executa a ação pendente após aprovação do admin."""
    if approval.content_type == 'news':
        _execute_news(approval)
    elif approval.content_type == 'page':
        _execute_page(approval)
    else:
        raise ValueError(f'Tipo de conteúdo desconhecido: {approval.content_type}')


def _execute_news(approval: ContentApproval) -> None:
    from datetime import datetime as dt
    from app.models.news import News
    from app.models.audit import AuditLog

    news = db.session.get(News, approval.content_id)
    if not news:
        raise ValueError('Notícia não encontrada (pode ter sido excluída).')

    if approval.action == 'publish':
        news.is_published = True
        news.published_at = dt.utcnow()
        db.session.add(AuditLog(user_id=approval.reviewed_by_id, action='publish',
                                entity='news', entity_id=news.id,
                                new_values={'is_published': True}))

    elif approval.action == 'unpublish':
        news.is_published = False
        news.published_at = None
        db.session.add(AuditLog(user_id=approval.reviewed_by_id, action='unpublish',
                                entity='news', entity_id=news.id,
                                new_values={'is_published': False}))

    elif approval.action == 'delete':
        db.session.add(AuditLog(user_id=approval.reviewed_by_id, action='delete',
                                entity='news', entity_id=news.id,
                                new_values={'title': news.title}))
        db.session.delete(news)

    elif approval.action == 'edit':
        snap = approval.snapshot or {}
        _apply_news_snapshot(news, snap)
        db.session.add(AuditLog(user_id=approval.reviewed_by_id, action='update',
                                entity='news', entity_id=news.id,
                                new_values={'title': news.title}))


def _apply_news_snapshot(news, snap: dict) -> None:
    """Aplica um snapshot de edição de notícia."""
    from app.models.news import Category, Tag
    from app.services.news_service import _slugify  # type: ignore

    if 'title' in snap:
        news.title = snap['title']
        news.slug  = _slugify(snap['title'])
    if 'summary' in snap:
        news.summary = snap['summary']
    if 'content_json' in snap:
        news.content_json = snap['content_json']
    if 'featured_image' in snap:
        news.featured_image = snap['featured_image']
    if 'category_ids' in snap:
        cats = Category.query.filter(Category.id.in_(snap['category_ids'])).all()
        news.categories = cats
    if 'tag_names' in snap:
        tags = []
        for tname in snap['tag_names']:
            t = Tag.query.filter_by(name=tname).first()
            if not t:
                from app.services.news_service import _slugify
                t = Tag(name=tname, slug=_slugify(tname))
                db.session.add(t)
            tags.append(t)
        news.tags = tags


def _execute_page(approval: ContentApproval) -> None:
    from app.models.audit import AuditLog

    # Importa o modelo Page — pode estar em content ou pages dependendo do projeto
    try:
        from app.models.content import Page
    except ImportError:
        from app.models.pages import Page  # fallback

    page = db.session.get(Page, approval.content_id)
    if not page:
        raise ValueError('Página não encontrada (pode ter sido excluída).')

    if approval.action == 'publish':
        page.is_published = True
        db.session.add(AuditLog(user_id=approval.reviewed_by_id, action='publish',
                                entity='page', entity_id=page.id,
                                new_values={'is_published': True}))

    elif approval.action == 'unpublish':
        page.is_published = False
        db.session.add(AuditLog(user_id=approval.reviewed_by_id, action='unpublish',
                                entity='page', entity_id=page.id,
                                new_values={'is_published': False}))

    elif approval.action == 'delete':
        db.session.add(AuditLog(user_id=approval.reviewed_by_id, action='delete',
                                entity='page', entity_id=page.id,
                                new_values={'name': page.name}))
        db.session.delete(page)

    elif approval.action == 'edit':
        snap = approval.snapshot or {}
        if 'name' in snap:
            page.name = snap['name']
        if 'content_json' in snap:
            page.content_json = snap['content_json']
        if 'slug' in snap:
            page.slug = snap['slug']
        db.session.add(AuditLog(user_id=approval.reviewed_by_id, action='update',
                                entity='page', entity_id=page.id,
                                new_values={'name': page.name}))


# ─── Função auxiliar para criar solicitação (usada pelas rotas de conteúdo) ──

def request_approval(action: str, content_type: str, content_id: int,
                     content_title: str, requested_by_id: int,
                     snapshot: dict = None) -> ContentApproval:
    """Cria uma solicitação de aprovação e salva no banco."""
    # Cancela qualquer pendente anterior do mesmo tipo/ação/conteúdo
    ContentApproval.query.filter_by(
        action=action,
        content_type=content_type,
        content_id=content_id,
        status='pending',
    ).update({'status': 'rejected', 'review_note': 'Substituída por nova solicitação.'})

    approval = ContentApproval(
        action=action,
        content_type=content_type,
        content_id=content_id,
        content_title=content_title,
        requested_by_id=requested_by_id,
        snapshot=snapshot,
    )
    db.session.add(approval)
    db.session.commit()
    return approval
