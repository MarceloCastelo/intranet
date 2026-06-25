import json
import os
import re
import uuid
from datetime import datetime

from PIL import Image
from flask import current_app
from sqlalchemy import or_
from werkzeug.exceptions import BadRequest

from app import db
from app.models.audit import AuditLog
from app.models.news import Category, News, Tag

_ALLOWED_IMAGE_EXTS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
_ALLOWED_PDF_EXTS  = {'pdf'}


# ─── Helpers ────────────────────────────────────────────────────────────────

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
        q = News.query.filter_by(slug=candidate)
        if exclude_id:
            q = q.filter(News.id != exclude_id)
        if not q.first():
            return candidate
        candidate = f'{slug}-{n}'
        n += 1


def _save_featured_image(file_storage) -> str | None:
    if not file_storage or not file_storage.filename:
        return None
    ext = os.path.splitext(file_storage.filename)[1].lstrip('.').lower()
    if ext not in _ALLOWED_IMAGE_EXTS:
        raise BadRequest(f'Tipo de arquivo não permitido: .{ext}')
    upload_dir = os.path.join(current_app.root_path, '..', 'uploads', 'news')
    os.makedirs(upload_dir, exist_ok=True)
    filename = f"{uuid.uuid4().hex}.{ext}"
    path = os.path.join(upload_dir, filename)
    img = Image.open(file_storage)
    img.thumbnail((1200, 800))
    img.save(path, optimize=True, quality=85)
    return f'/uploads/news/{filename}'


def _save_pdf(file_storage) -> tuple:
    """Salva PDF em disco e retorna (filename, original_name, thumbnail_path)."""
    if not file_storage or not file_storage.filename:
        return None, None, None
    ext = os.path.splitext(file_storage.filename)[1].lstrip('.').lower()
    if ext not in _ALLOWED_PDF_EXTS:
        raise BadRequest(f'Tipo de arquivo não permitido: .{ext}')
    original_name = file_storage.filename
    upload_dir = os.path.join(current_app.root_path, '..', 'uploads', 'news', 'pdfs')
    os.makedirs(upload_dir, exist_ok=True)
    filename = f"{uuid.uuid4().hex}.pdf"
    pdf_path = os.path.join(upload_dir, filename)
    file_storage.save(pdf_path)

    thumbnail_url = _generate_pdf_thumbnail(pdf_path)
    return filename, original_name, thumbnail_url


def _generate_pdf_thumbnail(pdf_path: str) -> str | None:
    """Renderiza a primeira página do PDF como JPEG e retorna a URL pública."""
    try:
        import fitz  # PyMuPDF
        doc = fitz.open(pdf_path)
        page = doc.load_page(0)
        mat = fitz.Matrix(1.5, 1.5)  # 108 DPI (72 × 1.5)
        pix = page.get_pixmap(matrix=mat, alpha=False)
        doc.close()

        img_dir = os.path.join(current_app.root_path, '..', 'uploads', 'news')
        os.makedirs(img_dir, exist_ok=True)
        img_filename = f"{uuid.uuid4().hex}.jpg"
        img_path = os.path.join(img_dir, img_filename)

        from PIL import Image as PILImage
        import io
        img = PILImage.open(io.BytesIO(pix.tobytes("jpeg")))
        img.thumbnail((800, 1000))
        img.save(img_path, format='JPEG', optimize=True, quality=82)
        return f'/uploads/news/{img_filename}'
    except Exception:
        return None


def _delete_pdf_file(filename: str) -> None:
    if not filename:
        return
    path = os.path.join(current_app.root_path, '..', 'uploads', 'news', 'pdfs', filename)
    try:
        if os.path.exists(path):
            os.remove(path)
    except OSError:
        pass


def _sync_tags(raw: str) -> list:
    """Recebe string CSV de tags, cria as que não existem e retorna lista de objetos Tag."""
    names = [t.strip().lower() for t in raw.split(',') if t.strip()]
    result = []
    for name in names:
        slug = _slugify(name)
        tag = Tag.query.filter_by(slug=slug).first()
        if not tag:
            tag = Tag(name=name[:50], slug=slug[:50])
            db.session.add(tag)
        result.append(tag)
    return result


# ─── Notícias ────────────────────────────────────────────────────────────────

def list_news(search: str = '', category_id: int = 0,
              published: str = '', page: int = 1):
    q = News.query.order_by(News.created_at.desc())

    if search:
        term = f'%{search}%'
        q = q.filter(or_(News.title.ilike(term), News.summary.ilike(term)))

    if category_id:
        q = q.filter(News.categories.any(id=category_id))

    if published == 'yes':
        q = q.filter(News.is_published == True)   # noqa: E712
    elif published == 'no':
        q = q.filter(News.is_published == False)  # noqa: E712

    return q.paginate(page=page, per_page=15, error_out=False)


def get_news_or_404(news_id: int) -> News:
    return db.get_or_404(News, news_id)


def create_news(form, author_id: int, force_draft: bool = False) -> News:
    slug = form.slug.data.strip() if form.slug.data and form.slug.data.strip() \
        else form.title.data
    slug = _unique_slug(slug)

    content_raw = form.content_json.data or ''
    try:
        content = json.loads(content_raw)
    except (json.JSONDecodeError, TypeError):
        content = {"type": "html", "content": content_raw}

    news = News(
        title=form.title.data.strip(),
        slug=slug,
        summary=form.summary.data.strip() if form.summary.data else None,
        content_json=content,
        featured_image_size=form.featured_image_size.data or 'banner',
        author_id=author_id,
    )

    image = _save_featured_image(form.featured_image.data)
    if image:
        news.featured_image = image

    if form.categories.data:
        news.categories = Category.query.filter(Category.id.in_(form.categories.data)).all()

    if form.tags_input.data:
        news.tags = _sync_tags(form.tags_input.data)

    if form.is_published.data and not force_draft:
        news.is_published = True
        news.published_at = datetime.utcnow()

    db.session.add(news)
    db.session.flush()

    db.session.add(AuditLog(
        user_id=author_id,
        action='create',
        entity='news',
        entity_id=news.id,
        new_values={'title': news.title},
    ))
    db.session.commit()
    return news


def update_news(news: News, form, actor_id: int) -> News:
    news.title = form.title.data.strip()

    new_slug = form.slug.data.strip() if form.slug.data and form.slug.data.strip() \
        else form.title.data
    news.slug = _unique_slug(new_slug, exclude_id=news.id)

    news.summary = form.summary.data.strip() if form.summary.data else None

    content_raw = form.content_json.data or ''
    try:
        news.content_json = json.loads(content_raw)
    except (json.JSONDecodeError, TypeError):
        news.content_json = {"type": "html", "content": content_raw}

    news.featured_image_size = form.featured_image_size.data or 'banner'

    image = _save_featured_image(form.featured_image.data)
    if image:
        news.featured_image = image

    if form.categories.data is not None:
        news.categories = Category.query.filter(Category.id.in_(form.categories.data)).all()

    if form.tags_input.data is not None:
        news.tags = _sync_tags(form.tags_input.data) if form.tags_input.data.strip() else []

    was_published = news.is_published
    news.is_published = form.is_published.data
    if news.is_published and not was_published:
        news.published_at = datetime.utcnow()
    elif not news.is_published:
        news.published_at = None

    db.session.add(AuditLog(
        user_id=actor_id,
        action='update',
        entity='news',
        entity_id=news.id,
        new_values={'title': news.title},
    ))
    db.session.commit()
    return news


def create_pdf_news(form, pdf_files: list, author_id: int) -> News:
    from app.models.news import NewsPdf
    slug = _unique_slug(form.title.data)

    news = News(
        title=form.title.data.strip(),
        slug=slug,
        content_json={'type': 'pdf_news'},
        news_type='pdf',
        author_id=author_id,
    )

    if form.is_published.data:
        news.is_published = True
        news.published_at = datetime.utcnow()

    db.session.add(news)
    db.session.flush()

    first_thumbnail = None
    for fs in pdf_files:
        filename, original_name, thumbnail_url = _save_pdf(fs)
        if filename:
            if first_thumbnail is None and thumbnail_url:
                first_thumbnail = thumbnail_url
            db.session.add(NewsPdf(
                news_id=news.id,
                filename=filename,
                original_name=original_name,
                file_path=f'/uploads/news/pdfs/{filename}',
            ))

    if first_thumbnail:
        news.featured_image = first_thumbnail

    db.session.add(AuditLog(
        user_id=author_id,
        action='create',
        entity='news',
        entity_id=news.id,
        new_values={'title': news.title, 'news_type': 'pdf'},
    ))
    db.session.commit()
    return news


def update_pdf_news(news: News, form, new_pdf_files: list,
                    remove_pdf_ids: list, actor_id: int) -> News:
    from app.models.news import NewsPdf

    news.title = form.title.data.strip()
    news.slug  = _unique_slug(form.title.data, exclude_id=news.id)

    was_published = news.is_published
    news.is_published = form.is_published.data
    if news.is_published and not was_published:
        news.published_at = datetime.utcnow()
    elif not news.is_published:
        news.published_at = None

    # Remove PDFs marcados para exclusão
    deleted_filenames = []
    if remove_pdf_ids:
        to_remove = NewsPdf.query.filter(
            NewsPdf.id.in_(remove_pdf_ids),
            NewsPdf.news_id == news.id,
        ).all()
        for pdf in to_remove:
            deleted_filenames.append(pdf.filename)
            db.session.delete(pdf)

    # Adiciona novos PDFs
    new_thumbnail = None
    for fs in new_pdf_files:
        filename, original_name, thumbnail_url = _save_pdf(fs)
        if filename:
            if new_thumbnail is None and thumbnail_url:
                new_thumbnail = thumbnail_url
            db.session.add(NewsPdf(
                news_id=news.id,
                filename=filename,
                original_name=original_name,
                file_path=f'/uploads/news/pdfs/{filename}',
            ))

    # Atualiza thumbnail: usa o novo se houver, senão mantém o existente
    if new_thumbnail:
        news.featured_image = new_thumbnail

    db.session.add(AuditLog(
        user_id=actor_id,
        action='update',
        entity='news',
        entity_id=news.id,
        new_values={'title': news.title, 'news_type': 'pdf'},
    ))
    db.session.commit()

    for fn in deleted_filenames:
        _delete_pdf_file(fn)

    return news


def delete_news(news: News, actor_id: int) -> None:
    pdf_filenames = [p.filename for p in news.pdfs] if news.news_type == 'pdf' else []
    db.session.add(AuditLog(
        user_id=actor_id,
        action='delete',
        entity='news',
        entity_id=news.id,
        new_values={'title': news.title},
    ))
    db.session.delete(news)
    db.session.commit()
    for fn in pdf_filenames:
        _delete_pdf_file(fn)


def toggle_publish(news: News, actor_id: int) -> News:
    news.is_published = not news.is_published
    news.published_at = datetime.utcnow() if news.is_published else None
    db.session.add(AuditLog(
        user_id=actor_id,
        action='publish' if news.is_published else 'unpublish',
        entity='news',
        entity_id=news.id,
        new_values={'title': news.title, 'is_published': news.is_published},
    ))
    db.session.commit()
    return news


# ─── Categorias ──────────────────────────────────────────────────────────────

def all_categories() -> list:
    return Category.query.order_by(Category.name).all()


def create_category(form) -> Category:
    slug = _slugify(form.slug.data.strip() if form.slug.data and form.slug.data.strip()
                    else form.name.data)
    cat = Category(name=form.name.data.strip(), slug=slug)
    db.session.add(cat)
    db.session.commit()
    return cat


def record_view(news: News, user_id: int | None, ip: str) -> None:
    """Incrementa contador e grava NewsView (sem duplicar por IP na mesma hora)."""
    from app.models.news import NewsView
    from datetime import timedelta
    cutoff = datetime.utcnow() - timedelta(hours=1)
    already = NewsView.query.filter(
        NewsView.news_id == news.id,
        NewsView.ip_address == ip,
        NewsView.viewed_at >= cutoff,
    ).first()
    if not already:
        db.session.add(NewsView(news_id=news.id, user_id=user_id, ip_address=ip))
        news.views_count = (news.views_count or 0) + 1
        db.session.commit()
