from app import db
from app.models.communication import Service


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


def create_service(form, actor_id: int) -> Service:
    svc = Service(
        title          = form.title.data.strip(),
        url            = form.url.data.strip(),
        description    = form.description.data or None,
        category       = (form.category.data or 'Geral').strip(),
        color          = form.color.data,
        icon_url       = form.icon_url.data or None,
        target_blank   = form.target_blank.data,
        order_position = form.order_position.data or 0,
        is_active      = form.is_active.data,
        created_by     = actor_id,
    )
    db.session.add(svc)
    db.session.commit()
    return svc


def update_service(svc: Service, form) -> Service:
    svc.title          = form.title.data.strip()
    svc.url            = form.url.data.strip()
    svc.description    = form.description.data or None
    svc.category       = (form.category.data or 'Geral').strip()
    svc.color          = form.color.data
    svc.icon_url       = form.icon_url.data or None
    svc.target_blank   = form.target_blank.data
    svc.order_position = form.order_position.data or 0
    svc.is_active      = form.is_active.data
    db.session.commit()
    return svc


def delete_service(svc: Service) -> None:
    db.session.delete(svc)
    db.session.commit()
