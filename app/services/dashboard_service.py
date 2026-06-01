from datetime import date, datetime

from sqlalchemy import extract, func

from app import cache, db
from app.models.event import Event
from app.models.news import News
from app.models.user import User

_DAYS_PT = ['Segunda-feira', 'Terça-feira', 'Quarta-feira', 'Quinta-feira',
            'Sexta-feira', 'Sábado', 'Domingo']
_MONTHS_PT = ['janeiro', 'fevereiro', 'março', 'abril', 'maio', 'junho',
              'julho', 'agosto', 'setembro', 'outubro', 'novembro', 'dezembro']


def _date_pt(d: date) -> str:
    return f"{_DAYS_PT[d.weekday()]}, {d.day:02d} de {_MONTHS_PT[d.month - 1]} de {d.year}"


@cache.cached(timeout=60, key_prefix='dashboard_data')
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
    from datetime import timedelta
    cutoff_30d = datetime.now() - timedelta(days=30)
    new_users = (
        db.session.query(func.count(User.id))
        .filter(User.created_at >= cutoff_30d)
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
        'recent_news':     recent_news,
        'upcoming_events': upcoming_events,
        'birthdays':       birthdays,
        'today':           today,
        'today_str':       _date_pt(today),
        'current_month_pt': _MONTHS_PT[today.month - 1].capitalize(),
    }
