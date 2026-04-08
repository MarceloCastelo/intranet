from datetime import datetime

from flask import current_app
from sqlalchemy import func

from app import db
from app.models.content import Poll, PollOption, PollVote


# ─── Listagem / busca ─────────────────────────────────────────────────────────

def list_polls(page: int = 1):
    return (Poll.query
            .order_by(Poll.created_at.desc())
            .paginate(page=page, per_page=20, error_out=False))


def active_polls():
    now = datetime.utcnow()
    return (Poll.query
            .filter(Poll.is_active.is_(True))
            .filter(db.or_(Poll.expires_at.is_(None), Poll.expires_at > now))
            .order_by(Poll.created_at.desc())
            .all())


def get_poll_or_404(poll_id: int) -> Poll:
    return db.get_or_404(Poll, poll_id)


# ─── CRUD ─────────────────────────────────────────────────────────────────────

def create_poll(form, actor_id: int) -> Poll:
    poll = Poll(
        question    = form.question.data.strip(),
        description = form.description.data or None,
        is_multiple = form.is_multiple.data,
        is_active   = form.is_active.data,
        expires_at  = form.expires_at.data or None,
        created_by  = actor_id,
    )
    db.session.add(poll)
    db.session.flush()  # gera poll.id antes de adicionar opções

    for i, opt_form in enumerate(form.options):
        text = opt_form.option_text.data.strip() if opt_form.option_text.data else ''
        if text:
            db.session.add(PollOption(
                poll_id        = poll.id,
                option_text    = text,
                order_position = opt_form.order_position.data or i,
            ))

    db.session.commit()
    return poll


def update_poll(poll: Poll, form) -> Poll:
    poll.question    = form.question.data.strip()
    poll.description = form.description.data or None
    poll.is_multiple = form.is_multiple.data
    poll.is_active   = form.is_active.data
    poll.expires_at  = form.expires_at.data or None

    # Remove opções antigas e recria
    for opt in list(poll.options):
        db.session.delete(opt)
    db.session.flush()

    for i, opt_form in enumerate(form.options):
        text = opt_form.option_text.data.strip() if opt_form.option_text.data else ''
        if text:
            db.session.add(PollOption(
                poll_id        = poll.id,
                option_text    = text,
                order_position = opt_form.order_position.data or i,
            ))

    db.session.commit()
    return poll


def delete_poll(poll: Poll) -> None:
    db.session.delete(poll)
    db.session.commit()


# ─── Votação ──────────────────────────────────────────────────────────────────

def user_voted(poll_id: int, user_id: int) -> bool:
    return db.session.query(
        PollVote.query.filter_by(poll_id=poll_id, user_id=user_id).exists()
    ).scalar()


def cast_vote(poll: Poll, option_ids: list[int], user_id: int):
    """Registra o voto. Se já votou, retorna False sem fazer nada."""
    if user_voted(poll.id, user_id):
        return False

    valid_ids = {o.id for o in poll.options}
    if not poll.is_multiple:
        option_ids = option_ids[:1]

    for oid in option_ids:
        if oid in valid_ids:
            db.session.add(PollVote(poll_id=poll.id, option_id=oid, user_id=user_id))

    db.session.commit()
    return True


# ─── Resultados ───────────────────────────────────────────────────────────────

def poll_results(poll: Poll) -> dict:
    """Retorna dict com total de votos e percentual por opção."""
    counts = {
        row.option_id: row.total
        for row in db.session.query(
            PollVote.option_id,
            func.count(PollVote.id).label('total')
        ).filter(PollVote.poll_id == poll.id).group_by(PollVote.option_id).all()
    }
    total = sum(counts.values())
    options = sorted(poll.options, key=lambda o: o.order_position)
    results = []
    for opt in options:
        c = counts.get(opt.id, 0)
        results.append({
            'id':      opt.id,
            'text':    opt.option_text,
            'votes':   c,
            'percent': round(c / total * 100) if total else 0,
        })
    return {'total': total, 'options': results}
