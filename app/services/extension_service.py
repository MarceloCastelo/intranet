from app import db
from app.models.communication import PhoneExtension
from app.models.user import Department, User


def _dept_choices():
    depts = Department.query.order_by(Department.name).all()
    return [(0, '— Nenhum —')] + [(d.id, d.name) for d in depts]


def _user_choices():
    users = (User.query
             .filter(User.status == 'active')
             .order_by(User.name)
             .all())
    return [(0, '— Nenhum —')] + [(u.id, u.name) for u in users]


def set_form_choices(form):
    form.department_id.choices = _dept_choices()
    form.user_id.choices       = _user_choices()


# ─── Consultas ────────────────────────────────────────────────────────────────

def list_extensions(search: str = '') -> list:
    q = PhoneExtension.query
    if search:
        like = f'%{search}%'
        q = q.filter(
            db.or_(
                PhoneExtension.name.ilike(like),
                PhoneExtension.extension.ilike(like),
            )
        )
    return q.order_by(PhoneExtension.order_position, PhoneExtension.name).all()


def get_extension_or_404(ext_id: int) -> PhoneExtension:
    return db.get_or_404(PhoneExtension, ext_id)


# ─── CRUD ─────────────────────────────────────────────────────────────────────

def create_extension(form, actor_id: int) -> PhoneExtension:
    ext = PhoneExtension(
        name           = form.name.data.strip(),
        extension      = form.extension.data.strip(),
        department_id  = form.department_id.data or None,
        user_id        = form.user_id.data or None,
        notes          = form.notes.data or None,
        order_position = form.order_position.data or 0,
        is_active      = form.is_active.data,
        created_by     = actor_id,
    )
    db.session.add(ext)
    db.session.commit()
    return ext


def update_extension(ext: PhoneExtension, form) -> PhoneExtension:
    ext.name           = form.name.data.strip()
    ext.extension      = form.extension.data.strip()
    ext.department_id  = form.department_id.data or None
    ext.user_id        = form.user_id.data or None
    ext.notes          = form.notes.data or None
    ext.order_position = form.order_position.data or 0
    ext.is_active      = form.is_active.data
    db.session.commit()
    return ext


def delete_extension(ext: PhoneExtension) -> None:
    db.session.delete(ext)
    db.session.commit()
