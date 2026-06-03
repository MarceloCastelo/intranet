from flask import (Blueprint, flash, jsonify, redirect, render_template,
                   request, url_for)
from flask_login import current_user, login_required

from app.forms.polls import PollForm
from app.services.poll_service import (cast_vote, create_poll, delete_poll,
                                        get_poll_or_404, list_polls,
                                        poll_results, update_poll, user_voted)
from app.utils.decorators import admin_required, editor_or_admin_required

polls_bp = Blueprint('polls', __name__, url_prefix='/enquetes')


# ─── Admin ────────────────────────────────────────────────────────────────────

@polls_bp.route('/')
@login_required
def public_list():
    from app.services.poll_service import active_polls
    polls = active_polls()
    return render_template('polls/public_list.html', polls=polls)


@polls_bp.route('/admin')
@login_required
@editor_or_admin_required
def index():
    page       = request.args.get('page', 1, type=int)
    pagination = list_polls(page=page)
    return render_template('polls/index.html', pagination=pagination)


@polls_bp.route('/admin/criar', methods=['GET', 'POST'])
@login_required
@editor_or_admin_required
def create():
    form = PollForm()
    # Garante ao menos 2 campos de opção na primeira exibição
    while len(form.options) < 2:
        form.options.append_entry()

    if form.validate_on_submit():
        poll = create_poll(form, actor_id=current_user.id)
        flash('Enquete criada.', 'success')
        return redirect(url_for('polls.detail', poll_id=poll.id))
    return render_template('polls/form.html', form=form, title='Nova enquete', poll=None)


@polls_bp.route('/admin/<int:poll_id>/editar', methods=['GET', 'POST'])
@login_required
@editor_or_admin_required
def edit(poll_id):
    poll = get_poll_or_404(poll_id)
    form = PollForm(obj=poll)

    if request.method == 'GET':
        # Preenche FieldList com as opções existentes
        form.options.entries.clear()
        for opt in sorted(poll.options, key=lambda o: o.order_position):
            form.options.append_entry({
                'option_text':    opt.option_text,
                'order_position': opt.order_position,
            })
        if len(form.options) < 2:
            form.options.append_entry()

    if form.validate_on_submit():
        update_poll(poll, form)
        flash('Enquete atualizada.', 'success')
        return redirect(url_for('polls.detail', poll_id=poll.id))
    return render_template('polls/form.html', form=form, title='Editar enquete', poll=poll)


@polls_bp.route('/admin/<int:poll_id>/excluir', methods=['POST'])
@login_required
@editor_or_admin_required
def delete(poll_id):
    poll = get_poll_or_404(poll_id)
    delete_poll(poll)
    flash('Enquete excluída.', 'success')
    return redirect(url_for('polls.index'))


# ─── Visualização pública / votação ───────────────────────────────────────────

@polls_bp.route('/<int:poll_id>')
@login_required
def detail(poll_id):
    poll    = get_poll_or_404(poll_id)
    voted   = user_voted(poll.id, current_user.id)
    results = poll_results(poll)
    return render_template('polls/detail.html', poll=poll, voted=voted, results=results)


@polls_bp.route('/<int:poll_id>/votar', methods=['POST'])
@login_required
def vote(poll_id):
    poll = get_poll_or_404(poll_id)

    if not poll.is_active:
        flash('Esta enquete está encerrada.', 'warning')
        return redirect(url_for('polls.detail', poll_id=poll_id))

    option_ids = request.form.getlist('option_id', type=int)
    if not option_ids:
        flash('Selecione ao menos uma opção.', 'warning')
        return redirect(url_for('polls.detail', poll_id=poll_id))

    ok = cast_vote(poll, option_ids, current_user.id)
    if not ok:
        flash('Você já votou nesta enquete.', 'info')
    else:
        flash('Voto registrado!', 'success')
    return redirect(url_for('polls.detail', poll_id=poll_id))
