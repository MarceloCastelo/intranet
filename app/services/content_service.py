import os
import uuid
from datetime import date
from types import SimpleNamespace

import bleach
from PIL import Image
from flask import current_app
from werkzeug.exceptions import BadRequest

from app import db
from app.models.content import Banner, Faq, FaqCategory
from app.models.event import Event
from app.models.user import User

_ALLOWED_IMAGE_EXTS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

# Tags HTML permitidas no corpo de respostas do FAQ (editor de texto rico)
_FAQ_ALLOWED_TAGS = [
    'p', 'br', 'strong', 'em', 'u', 'ul', 'ol', 'li',
    'h1', 'h2', 'h3', 'h4', 'blockquote', 'a', 'code', 'pre',
]
_FAQ_ALLOWED_ATTRS = {'a': ['href', 'title', 'target']}


def _sanitize_answer(html: str) -> str:
    """Remove tags/atributos perigosos preservando formatação do editor rico."""
    return bleach.clean(html, tags=_FAQ_ALLOWED_TAGS, attributes=_FAQ_ALLOWED_ATTRS, strip=True)

# ─── Helpers ─────────────────────────────────────────────────────────────────

def _save_image(file_storage, subfolder: str, size: tuple = (1200, 500)) -> str | None:
    if not file_storage or not file_storage.filename:
        return None
    ext = os.path.splitext(file_storage.filename)[1].lstrip('.').lower()
    if ext not in _ALLOWED_IMAGE_EXTS:
        raise BadRequest(f'Tipo de arquivo não permitido: .{ext}')
    upload_dir = os.path.join(current_app.root_path, '..', 'uploads', subfolder)
    os.makedirs(upload_dir, exist_ok=True)
    filename = f"{uuid.uuid4().hex}.{ext}"
    path = os.path.join(upload_dir, filename)
    img = Image.open(file_storage)
    img.thumbnail(size)
    img.save(path, optimize=True, quality=85)
    return f'/uploads/{subfolder}/{filename}'


# ─── Banners ──────────────────────────────────────────────────────────────────

def list_banners() -> list:
    return Banner.query.order_by(Banner.order_position, Banner.id).all()


def active_banners() -> list:
    today = date.today()
    q = Banner.query.filter(Banner.is_active == True, Banner.show_on_home == True)  # noqa: E712
    q = q.filter(
        db.or_(Banner.start_date == None, Banner.start_date <= today),  # noqa: E711
        db.or_(Banner.end_date   == None, Banner.end_date   >= today),  # noqa: E711
    )
    return q.order_by(Banner.order_position).all()


def get_banner_or_404(banner_id: int) -> Banner:
    return db.get_or_404(Banner, banner_id)


def create_banner(form, actor_id: int, force_inactive: bool = False) -> Banner:
    banner = Banner(
        title          = form.title.data or None,
        description    = form.description.data or None,
        link_url       = form.link_url.data or None,
        link_text      = form.link_text.data or None,
        target_blank   = form.target_blank.data,
        order_position = form.order_position.data or 0,
        is_active      = False if force_inactive else form.is_active.data,
        show_on_home   = form.show_on_home.data,
        start_date     = form.start_date.data or None,
        end_date       = form.end_date.data or None,
        created_by     = actor_id,
    )
    image = _save_image(form.image.data, 'banners')
    if image:
        banner.image_path = image
    db.session.add(banner)
    db.session.commit()
    return banner


def update_banner(banner: Banner, form) -> Banner:
    banner.title          = form.title.data or None
    banner.description    = form.description.data or None
    banner.link_url       = form.link_url.data or None
    banner.link_text      = form.link_text.data or None
    banner.target_blank   = form.target_blank.data
    banner.order_position = form.order_position.data or 0
    banner.is_active      = form.is_active.data
    banner.show_on_home   = form.show_on_home.data
    banner.start_date     = form.start_date.data or None
    banner.end_date       = form.end_date.data or None
    image = _save_image(form.image.data, 'banners')
    if image:
        banner.image_path = image
    db.session.commit()
    return banner


def delete_banner(banner: Banner) -> None:
    db.session.delete(banner)
    db.session.commit()


# ─── FAQ ──────────────────────────────────────────────────────────────────────

def all_faq_categories() -> list:
    return FaqCategory.query.order_by(FaqCategory.order_position, FaqCategory.name).all()


def active_faq_categories() -> list:
    return (FaqCategory.query
            .filter(FaqCategory.is_active == True)  # noqa: E712
            .order_by(FaqCategory.order_position)
            .all())


def get_faq_or_404(faq_id: int) -> Faq:
    return db.get_or_404(Faq, faq_id)


def get_faq_category_or_404(cat_id: int) -> FaqCategory:
    return db.get_or_404(FaqCategory, cat_id)


def create_faq_category(form) -> FaqCategory:
    cat = FaqCategory(
        name           = form.name.data.strip(),
        description    = form.description.data or None,
        order_position = form.order_position.data or 0,
        is_active      = form.is_active.data,
    )
    db.session.add(cat)
    db.session.commit()
    return cat


def update_faq_category(cat: FaqCategory, form) -> FaqCategory:
    cat.name           = form.name.data.strip()
    cat.description    = form.description.data or None
    cat.order_position = form.order_position.data or 0
    cat.is_active      = form.is_active.data
    db.session.commit()
    return cat


def delete_faq_category(cat: FaqCategory) -> None:
    db.session.delete(cat)
    db.session.commit()


def create_faq(form, actor_id: int, force_inactive: bool = False) -> Faq:
    faq = Faq(
        category_id    = form.category_id.data or None,
        question       = form.question.data.strip(),
        answer         = _sanitize_answer(form.answer.data.strip()),
        order_position = form.order_position.data or 0,
        is_active      = False if force_inactive else form.is_active.data,
        created_by     = actor_id,
    )
    db.session.add(faq)
    db.session.commit()
    return faq


def update_faq(faq: Faq, form) -> Faq:
    faq.category_id    = form.category_id.data or None
    faq.question       = form.question.data.strip()
    faq.answer         = _sanitize_answer(form.answer.data.strip())
    faq.order_position = form.order_position.data or 0
    faq.is_active      = form.is_active.data
    db.session.commit()
    return faq


def delete_faq(faq: Faq) -> None:
    db.session.delete(faq)
    db.session.commit()


# ─── Eventos ──────────────────────────────────────────────────────────────────

def list_events(upcoming_only: bool = False, page: int = 1):
    q = Event.query
    if upcoming_only:
        q = q.filter(Event.event_date >= date.today(), Event.is_active == True)  # noqa: E712
    return q.order_by(Event.event_date.desc()).paginate(page=page, per_page=20, error_out=False)


def events_for_year(year: int) -> list:
    from datetime import date as date_cls
    real_events = (Event.query
                   .filter(Event.event_date >= date_cls(year, 1, 1),
                           Event.event_date <= date_cls(year, 12, 31))
                   .order_by(Event.event_date, Event.event_time)
                   .all())

    # Aniversários de usuários ativos
    birthday_users = (User.query
                      .filter(User.status == 'active',
                              User.birth_date != None)  # noqa: E711
                      .all())

    synthetic = []
    for u in birthday_users:
        try:
            ev_date = date_cls(year, u.birth_date.month, u.birth_date.day)
        except ValueError:
            # 29/fev em ano não bissexto — pula
            continue
        obj = SimpleNamespace(
            id         = f'bday_{u.id}',
            title      = f'🎂 {u.name}',
            event_type = 'birthday',
            event_date = ev_date,
            event_time = None,
            location   = None,
        )
        synthetic.append(obj)

    combined = real_events + synthetic
    combined.sort(key=lambda e: (e.event_date, e.event_time or __import__('datetime').time.min))
    return combined


def get_event_or_404(event_id: int) -> Event:
    return db.get_or_404(Event, event_id)


def create_event(form, actor_id: int, force_inactive: bool = False) -> Event:
    event = Event(
        title        = form.title.data.strip(),
        description  = {'text': form.description.data} if form.description.data else None,
        event_date   = form.event_date.data,
        event_time   = form.event_time.data or None,
        end_date     = form.end_date.data or None,
        location     = form.location.data or None,
        location_url = form.location_url.data or None,
        event_type   = form.event_type.data,
        is_active    = False if force_inactive else form.is_active.data,
        created_by   = actor_id,
    )
    db.session.add(event)
    db.session.commit()
    return event


def update_event(event: Event, form) -> Event:
    event.title        = form.title.data.strip()
    event.description  = {'text': form.description.data} if form.description.data else None
    event.event_date   = form.event_date.data
    event.event_time   = form.event_time.data or None
    event.end_date     = form.end_date.data or None
    event.location     = form.location.data or None
    event.location_url = form.location_url.data or None
    event.event_type   = form.event_type.data
    event.is_active    = form.is_active.data
    db.session.commit()
    return event


def delete_event(event: Event) -> None:
    db.session.delete(event)
    db.session.commit()
