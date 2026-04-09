from flask import abort

from app import db
from app.models.news import Comment, Reaction

VALID_ENTITIES = {'news', 'event', 'gallery'}
VALID_EMOJIS   = {'like', 'love', 'clap', 'laugh', 'sad'}
EMOJI_LABELS   = {
    'like':  ('👍', 'Curtir'),
    'love':  ('❤️',  'Amei'),
    'clap':  ('👏', 'Parabéns'),
    'laugh': ('😂', 'Haha'),
    'sad':   ('😢', 'Triste'),
}


# ─── Comentários ──────────────────────────────────────────────────────────────

def get_comments(entity_type: str, entity_id: int) -> list[Comment]:
    return (Comment.query
            .filter_by(entity_type=entity_type, entity_id=entity_id, is_approved=True)
            .order_by(Comment.created_at)
            .all())


def add_comment(entity_type: str, entity_id: int, user_id: int, body: str) -> Comment:
    body = body.strip()
    if not body or len(body) > 2000:
        abort(400)
    c = Comment(entity_type=entity_type, entity_id=entity_id,
                user_id=user_id, content=body)
    db.session.add(c)
    db.session.commit()
    return c


def delete_comment(comment_id: int, actor_id: int, actor_role: str) -> None:
    c = Comment.query.get_or_404(comment_id)
    if c.user_id != actor_id and actor_role not in ('admin', 'editor'):
        abort(403)
    db.session.delete(c)
    db.session.commit()


# ─── Reações ──────────────────────────────────────────────────────────────────

def get_reactions(entity_type: str, entity_id: int) -> dict:
    """Retorna {emoji: count} para todos os emojis."""
    counts = {e: 0 for e in VALID_EMOJIS}
    rows = (db.session.query(Reaction.emoji, db.func.count(Reaction.id))
            .filter_by(entity_type=entity_type, entity_id=entity_id)
            .group_by(Reaction.emoji)
            .all())
    for emoji, count in rows:
        counts[emoji] = count
    return counts


def get_user_reaction(entity_type: str, entity_id: int, user_id: int) -> str | None:
    """Retorna o emoji que o usuário reagiu, ou None."""
    r = Reaction.query.filter_by(
        entity_type=entity_type, entity_id=entity_id, user_id=user_id
    ).first()
    return r.emoji if r else None


def toggle_reaction(entity_type: str, entity_id: int,
                    user_id: int, emoji: str) -> str | None:
    """
    Alterna a reação:
    - Sem reação → adiciona
    - Mesma reação → remove
    - Reação diferente → troca
    Retorna o emoji atual (None se removeu).
    """
    if emoji not in VALID_EMOJIS:
        abort(400)
    existing = Reaction.query.filter_by(
        entity_type=entity_type, entity_id=entity_id, user_id=user_id
    ).first()
    if existing:
        if existing.emoji == emoji:
            db.session.delete(existing)
            db.session.commit()
            return None
        existing.emoji = emoji
        db.session.commit()
        return emoji
    r = Reaction(entity_type=entity_type, entity_id=entity_id,
                 user_id=user_id, emoji=emoji)
    db.session.add(r)
    db.session.commit()
    return emoji


# ─── Helper para carregar contexto no view ────────────────────────────────────

def interaction_context(entity_type: str, entity_id: int, user_id: int) -> dict:
    """Retorna dict pronto para passar ao template."""
    return {
        'comments':      get_comments(entity_type, entity_id),
        'reactions':     get_reactions(entity_type, entity_id),
        'user_reaction': get_user_reaction(entity_type, entity_id, user_id),
        'entity_type':   entity_type,
        'entity_id':     entity_id,
        'emoji_labels':  EMOJI_LABELS,
    }
