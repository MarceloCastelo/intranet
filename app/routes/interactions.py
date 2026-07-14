from flask import Blueprint, jsonify, request
from flask_login import current_user, login_required

from app.services.interaction_service import (
    add_comment, delete_comment, get_reactions,
    get_user_reaction, toggle_reaction,
)
from app.utils.timezone import to_local

interactions_bp = Blueprint('interactions', __name__, url_prefix='/interacoes')


@interactions_bp.route('/comentar', methods=['POST'])
@login_required
def comment():
    entity_type = request.form.get('entity_type', '').strip()
    entity_id   = request.form.get('entity_id',   0, type=int)
    body        = request.form.get('body',        '').strip()

    if entity_type not in ('news', 'event', 'gallery') or not entity_id or not body:
        return jsonify(ok=False, error='Dados inválidos.'), 400

    c = add_comment(entity_type, entity_id, current_user.id, body)
    return jsonify(
        ok=True,
        id=c.id,
        content=c.content,
        author=current_user.name,
        avatar=current_user.profile_picture or '',
        initial=current_user.name[0].upper(),
        created_at=to_local(c.created_at).strftime('%d/%m/%Y %H:%M'),
        can_delete=True,
    )


@interactions_bp.route('/comentarios/<int:comment_id>/excluir', methods=['POST'])
@login_required
def delete_comment_view(comment_id: int):
    delete_comment(comment_id, current_user.id, current_user.is_admin)
    return jsonify(ok=True)


@interactions_bp.route('/reagir', methods=['POST'])
@login_required
def react():
    entity_type = request.form.get('entity_type', '').strip()
    entity_id   = request.form.get('entity_id',   0, type=int)
    emoji       = request.form.get('emoji',       '').strip()

    if entity_type not in ('news', 'event', 'gallery') or not entity_id:
        return jsonify(ok=False, error='Dados inválidos.'), 400

    current = toggle_reaction(entity_type, entity_id, current_user.id, emoji)
    counts  = get_reactions(entity_type, entity_id)
    return jsonify(ok=True, user_reaction=current, counts=counts)
