import json
import re

from flask import current_app
from flask_login import current_user

from app import db
from app.models.audit import AuditLog
from app.models.content import Page


# ─── Helpers ─────────────────────────────────────────────────────────────────

def _slugify(text: str) -> str:
    text = text.lower().strip()
    for src, dst in [('àáâãä','a'),('èéêë','e'),('ìíîï','i'),('òóôõö','o'),('ùúûü','u'),('ç','c')]:
        for c in src:
            text = text.replace(c, dst)
    text = re.sub(r'[^a-z0-9\s-]', '', text)
    return re.sub(r'\s+', '-', text).strip('-')


def _unique_slug(base: str, exclude_id: int | None = None) -> str:
    slug = _slugify(base)
    candidate = slug
    n = 1
    while True:
        q = Page.query.filter_by(slug=candidate)
        if exclude_id:
            q = q.filter(Page.id != exclude_id)
        if not q.first():
            return candidate
        candidate = f'{slug}-{n}'
        n += 1


def _parse_content(raw) -> dict:
    if isinstance(raw, dict):
        return raw
    try:
        return json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return {'type': 'doc', 'content': []}


def tiptap_to_html(node: dict) -> str:
    """Converte um nó TipTap JSON em HTML para renderização server-side."""
    if not node or not isinstance(node, dict):
        return ''

    def _marks(text: str, marks: list) -> str:
        for m in (marks or []):
            t = m.get('type', '')
            if t == 'bold':
                text = f'<strong>{text}</strong>'
            elif t == 'italic':
                text = f'<em>{text}</em>'
            elif t == 'strike':
                text = f'<s>{text}</s>'
            elif t == 'code':
                text = f'<code>{text}</code>'
            elif t == 'link':
                href = m.get('attrs', {}).get('href', '#')
                text = f'<a href="{href}">{text}</a>'
        return text

    def _node(n: dict) -> str:
        t = n.get('type', '')
        children = ''.join(_node(c) for c in (n.get('content') or []))

        if t == 'doc':
            return children
        if t == 'text':
            return _marks(n.get('text', ''), n.get('marks'))
        if t == 'paragraph':
            return f'<p>{children}</p>' if children else '<p><br></p>'
        if t == 'heading':
            lvl = n.get('attrs', {}).get('level', 2)
            return f'<h{lvl}>{children}</h{lvl}>'
        if t == 'bulletList':
            return f'<ul>{children}</ul>'
        if t == 'orderedList':
            return f'<ol>{children}</ol>'
        if t == 'listItem':
            return f'<li>{children}</li>'
        if t == 'blockquote':
            return f'<blockquote>{children}</blockquote>'
        if t == 'codeBlock':
            return f'<pre><code>{children}</code></pre>'
        if t == 'horizontalRule':
            return '<hr>'
        if t == 'hardBreak':
            return '<br>'
        return children

    return _node(node)


# ─── Listagem ─────────────────────────────────────────────────────────────────

def list_pages(page: int = 1, search: str = ''):
    q = Page.query
    if search:
        like = f'%{search}%'
        q = q.filter(Page.name.ilike(like) | Page.title.ilike(like))
    return q.order_by(Page.name).paginate(page=page, per_page=20, error_out=False)


def all_published_pages():
    return Page.query.filter_by(is_published=True).order_by(Page.name).all()


def get_page_or_404(page_id: int) -> Page:
    return db.get_or_404(Page, page_id)


def get_page_by_slug(slug: str) -> Page | None:
    return Page.query.filter_by(slug=slug, is_published=True).first()


# ─── CRUD ─────────────────────────────────────────────────────────────────────

def create_page(form, actor_id: int, force_draft: bool = False) -> Page:
    slug = form.slug.data.strip() or form.name.data
    page = Page(
        name         = form.name.data.strip(),
        slug         = _unique_slug(slug),
        title        = form.title.data.strip(),
        content_json = _parse_content(form.content_json.data),
        is_published = form.is_published.data if not force_draft else False,
        created_by   = actor_id,
        updated_by   = actor_id,
    )
    db.session.add(page)
    db.session.flush()
    db.session.add(AuditLog(
        user_id   = actor_id,
        action    = 'create',
        entity    = 'pages',
        entity_id = page.id,
        new_values = {'name': page.name, 'slug': page.slug},
    ))
    db.session.commit()
    return page


def update_page(page: Page, form, actor_id: int) -> Page:
    page.name         = form.name.data.strip()
    page.slug         = _unique_slug(form.slug.data.strip() or form.name.data, exclude_id=page.id)
    page.title        = form.title.data.strip()
    page.content_json = _parse_content(form.content_json.data)
    page.is_published = form.is_published.data
    page.updated_by   = actor_id
    db.session.add(AuditLog(
        user_id    = actor_id,
        action     = 'update',
        entity     = 'pages',
        entity_id  = page.id,
        new_values = {'name': page.name, 'slug': page.slug},
    ))
    db.session.commit()
    return page


def delete_page(page: Page, actor_id: int) -> None:
    db.session.add(AuditLog(
        user_id    = actor_id,
        action     = 'delete',
        entity     = 'pages',
        entity_id  = page.id,
        new_values = {'name': page.name},
    ))
    db.session.delete(page)
    db.session.commit()
