import calendar as pycal
from datetime import date as date_cls

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app.forms.content import EventForm
from app.services.content_service import (create_event, delete_event,
                                           events_for_year, get_event_or_404,
                                           list_events, update_event)
from app.utils.decorators import editor_or_admin_required

events_bp = Blueprint('events', __name__, url_prefix='/eventos')


@events_bp.route('/')
@login_required
def public_list():
    from datetime import date as date_cls
    from app.models.event import Event
    events = (Event.query
              .filter(Event.is_active == True,
                      Event.event_date >= date_cls.today())
              .order_by(Event.event_date, Event.event_time)
              .limit(50).all())
    return render_template('events/public_list.html', events=events)


@events_bp.route('/<int:event_id>')
@login_required
def view(event_id: int):
    event = get_event_or_404(event_id)
    from app.services.interaction_service import interaction_context
    ctx = interaction_context('event', event.id, current_user.id)
    return render_template('events/view.html', event=event, **ctx)


@events_bp.route('/admin')
@login_required
@editor_or_admin_required
def index():
    page = request.args.get('page', 1, type=int)
    upcoming = request.args.get('upcoming', '')
    pagination = list_events(upcoming_only=(upcoming == '1'), page=page)
    return render_template('events/index.html', pagination=pagination, upcoming=upcoming)


@events_bp.route('/admin/criar', methods=['GET', 'POST'])
@login_required
@editor_or_admin_required
def create():
    form = EventForm()
    if form.validate_on_submit():
        event = create_event(form, actor_id=current_user.id)
        flash('Evento criado.', 'success')
        return redirect(url_for('events.index'))
    return render_template('events/form.html', form=form, title='Novo evento', event=None)


@events_bp.route('/admin/<int:event_id>/editar', methods=['GET', 'POST'])
@login_required
@editor_or_admin_required
def edit(event_id):
    event = get_event_or_404(event_id)
    form = EventForm(obj=event)
    if request.method == 'GET' and event.description:
        form.description.data = event.description.get('text', '')
    if form.validate_on_submit():
        update_event(event, form)
        flash('Evento atualizado.', 'success')
        return redirect(url_for('events.index'))
    return render_template('events/form.html', form=form, title='Editar evento', event=event)


@events_bp.route('/admin/<int:event_id>/excluir', methods=['POST'])
@login_required
@editor_or_admin_required
def delete(event_id):
    event = get_event_or_404(event_id)
    delete_event(event)
    flash('Evento excluído.', 'success')
    return redirect(url_for('events.index'))


# ─── Calendário ───────────────────────────────────────────────────────────────

_MONTHS_PT = ['Janeiro','Fevereiro','Março','Abril','Maio','Junho',
               'Julho','Agosto','Setembro','Outubro','Novembro','Dezembro']

_TYPE_COLOR = {
    'general':  'bg-gray-400',
    'meeting':  'bg-blue-500',
    'training': 'bg-amber-500',
    'holiday':  'bg-green-500',
    'birthday': 'bg-pink-500',
}


@events_bp.route('/calendario')
@login_required
def calendar_view():
    year   = request.args.get('year', date_cls.today().year, type=int)
    events = events_for_year(year)

    events_by_date = {}
    for ev in events:
        key = f"{ev.event_date.month}_{ev.event_date.day}"
        events_by_date.setdefault(key, []).append({
            'id':       ev.id,
            'title':    ev.title,
            'type':     ev.event_type,
            'color':    _TYPE_COLOR.get(ev.event_type, 'bg-gray-400'),
            'time':     ev.event_time.strftime('%H:%M') if ev.event_time else None,
            'location': ev.location,
        })

    cal = pycal.Calendar(firstweekday=6)   # semana começa no domingo
    months_data = []
    for m in range(1, 13):
        months_data.append({
            'month': m,
            'name':  _MONTHS_PT[m - 1],
            'weeks': cal.monthdayscalendar(year, m),
        })

    return render_template(
        'events/calendar.html',
        year=year,
        months_data=months_data,
        events_by_date=events_by_date,
        today=date_cls.today(),
    )
