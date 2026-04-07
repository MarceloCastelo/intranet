from datetime import date, datetime

from sqlalchemy import extract, func

from app import db
from app.models.event import Event
from app.models.news import News
from app.models.user import User


def get_dashboard_data() -> dict:
    today = date.today()

    # ── Contadores ────────────────────────────────────────────
    total_users      = db.session.query(func.count(User.id)).filter(User.status == 'active').scalar()
    total_news       = db.session.query(func.count(News.id)).filter(News.is_published == True).scalar()  # noqa: E712
    total_events     = (
        db.session.query(func.count(Event.id))
        .filter(Event.is_active == True, Event.event_date >= today)  # noqa: E712
        .scalar()
    )
    birthday_count   = (
        db.session.query(func.count(User.id))
        .filter(
            User.status == 'active',
            extract('month', User.birth_date) == today.month,
        )
        .scalar()
    )

    # ── Últimas 5 notícias publicadas ────────────────────────
    recent_news = (
        News.query
        .filter(News.is_published == True)  # noqa: E712
        .order_by(News.published_at.desc())
        .limit(5)
        .all()
    )

    # ── Próximos 5 eventos ───────────────────────────────────
    upcoming_events = (
        Event.query
        .filter(Event.is_active == True, Event.event_date >= today)  # noqa: E712
        .order_by(Event.event_date.asc(), Event.event_time.asc())
        .limit(5)
        .all()
    )

    # ── Aniversariantes do mês ───────────────────────────────
    birthdays = (
        User.query
        .filter(
            User.status == 'active',
            User.birth_date != None,  # noqa: E711
            extract('month', User.birth_date) == today.month,
        )
        .order_by(extract('day', User.birth_date).asc())
        .all()
    )

    # ── Novos usuários nos últimos 30 dias ───────────────────
    new_users = (
        db.session.query(func.count(User.id))
        .filter(User.created_at >= datetime(today.year, today.month, 1))
        .scalar()
    )

    return {
        'stats': {
            'total_users':    total_users,
            'total_news':     total_news,
            'total_events':   total_events,
            'birthday_count': birthday_count,
            'new_users':      new_users,
        },
        'recent_news':    recent_news,
        'upcoming_events': upcoming_events,
        'birthdays':      birthdays,
        'today':          today,
    }
