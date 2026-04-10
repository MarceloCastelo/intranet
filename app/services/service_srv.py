import os
import uuid

from werkzeug.utils import secure_filename

from app import db
from app.models.communication import Service


def _save_icon(file_storage, old_path: str | None = None) -> str:
    """Salva o arquivo de ícone e retorna o caminho relativo."""
    upload_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'uploads', 'services')
    os.makedirs(upload_dir, exist_ok=True)

    ext      = secure_filename(file_storage.filename).rsplit('.', 1)[-1].lower()
    filename = f"{uuid.uuid4().hex}.{ext}"
    file_storage.save(os.path.join(upload_dir, filename))

    if old_path:
        old_abs = os.path.join(os.path.dirname(__file__), '..', '..', old_path.lstrip('/'))
        if os.path.isfile(old_abs):
            os.remove(old_abs)

    return f'/uploads/services/{filename}'


def list_services_grouped(active_only: bool = True) -> dict:
    """Retorna dict {categoria: [Service, …]} ordenado."""
    q = Service.query
    if active_only:
        q = q.filter(Service.is_active == True)
    services = q.order_by(Service.category, Service.order_position, Service.title).all()

    grouped: dict = {}
    for svc in services:
        cat = svc.category or 'Geral'
        grouped.setdefault(cat, []).append(svc)
    return grouped


def list_all_services() -> list:
    return Service.query.order_by(Service.category, Service.order_position).all()


def get_service_or_404(svc_id: int) -> Service:
    return db.get_or_404(Service, svc_id)


def create_service(form, actor_id: int, force_inactive: bool = False) -> Service:
    icon = None
    if form.icon_url.data and form.icon_url.data.filename:
        icon = _save_icon(form.icon_url.data)

    svc = Service(
        title          = form.title.data.strip(),
        url            = form.url.data.strip(),
        description    = form.description.data or None,
        category       = (form.category.data or 'Geral').strip(),
        color          = form.color.data,
        icon_url       = icon,
        target_blank   = form.target_blank.data,
        order_position = form.order_position.data or 0,
        is_active      = False if force_inactive else form.is_active.data,
        created_by     = actor_id,
    )
    db.session.add(svc)
    db.session.commit()
    return svc


def update_service(svc: Service, form) -> Service:
    if form.icon_url.data and form.icon_url.data.filename:
        svc.icon_url = _save_icon(form.icon_url.data, svc.icon_url)

    svc.title          = form.title.data.strip()
    svc.url            = form.url.data.strip()
    svc.description    = form.description.data or None
    svc.category       = (form.category.data or 'Geral').strip()
    svc.color          = form.color.data
    svc.target_blank   = form.target_blank.data
    svc.order_position = form.order_position.data or 0
    svc.is_active      = form.is_active.data
    db.session.commit()
    return svc


def delete_service(svc: Service) -> None:
    db.session.delete(svc)
    db.session.commit()
