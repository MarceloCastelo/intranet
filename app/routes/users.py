from flask import (Blueprint, abort, flash, redirect,
                   render_template, request, url_for)
from flask_login import current_user, login_required

from app import db
from app.forms.user import AdminSetPasswordForm, BlockedIpForm, InviteUserForm, UserForm
from app.models.user import User
from app.services import user_service
from app.utils.decorators import admin_required

users_bp = Blueprint('users', __name__, url_prefix='/admin/usuarios')


# ─── Lista ────────────────────────────────────────────────────────────────────

@users_bp.route('/')
@login_required
@admin_required
def index():
    page    = request.args.get('page', 1, type=int)
    search  = request.args.get('q', '')
    role    = request.args.get('role', '')
    status  = request.args.get('status', '')
    dept_id = request.args.get('department_id', 0, type=int)

    pagination = user_service.list_users(
        search=search, role=role, status=status,
        department_id=dept_id, page=page,
    )
    departments = user_service.all_departments()
    return render_template(
        'users/index.html',
        pagination=pagination,
        departments=departments,
        search=search, role=role, status=status, dept_id=dept_id,
    )


# ─── Criar ────────────────────────────────────────────────────────────────────

@users_bp.route('/novo', methods=['GET', 'POST'])
@login_required
@admin_required
def create():
    departments = user_service.all_departments()
    form = UserForm(departments=departments)

    if form.validate_on_submit():
        email = form.email.data.strip().lower()
        if User.query.filter_by(email=email).first():
            form.email.errors.append('Este e-mail já está cadastrado.')
        else:
            user = user_service.create_user(form, current_user.id)
            flash(f'Usuário {user.name} criado com sucesso.', 'success')
            return redirect(url_for('users.detail', user_id=user.id))

    return render_template('users/form.html', form=form, title='Novo usuário')


# ─── Convidar ────────────────────────────────────────────────────────────────

@users_bp.route('/convidar', methods=['GET', 'POST'])
@login_required
@admin_required
def invite():
    departments = user_service.all_departments()
    form = InviteUserForm(departments=departments)

    if form.validate_on_submit():
        try:
            user = user_service.invite_user(form, current_user.id)
            flash(f'Convite enviado para {user.email}.', 'success')
            return redirect(url_for('users.index'))
        except ValueError as exc:
            form.email.errors.append(str(exc))

    return render_template('users/invite.html', form=form)


# ─── Detalhe ─────────────────────────────────────────────────────────────────

@users_bp.route('/<int:user_id>')
@login_required
@admin_required
def detail(user_id: int):
    user = db.session.get(User, user_id) or abort(404)
    return render_template('users/detail.html', user=user)


# ─── Editar ───────────────────────────────────────────────────────────────────

@users_bp.route('/<int:user_id>/editar', methods=['GET', 'POST'])
@login_required
@admin_required
def edit(user_id: int):
    user = db.session.get(User, user_id) or abort(404)
    departments = user_service.all_departments()
    form = UserForm(departments=departments, user_id=user.id, obj=user)

    # Pré-popula department_id no GET
    if request.method == 'GET':
        form.department_id.data = user.department_id or 0

    if form.validate_on_submit():
        try:
            user_service.update_user(user, form, current_user.id)
            flash('Usuário atualizado com sucesso.', 'success')
            return redirect(url_for('users.detail', user_id=user.id))
        except ValueError as exc:
            form.email.errors.append(str(exc))

    return render_template('users/form.html', form=form,
                           title=f'Editar — {user.name}', user=user)


# ─── Ações rápidas (POST) ─────────────────────────────────────────────────────

@users_bp.route('/<int:user_id>/status', methods=['POST'])
@login_required
@admin_required
def change_status(user_id: int):
    user = db.session.get(User, user_id) or abort(404)
    if user.id == current_user.id:
        flash('Você não pode alterar seu próprio status.', 'warning')
        return redirect(url_for('users.detail', user_id=user.id))

    new_status = request.form.get('status')
    if new_status not in ('active', 'inactive', 'blocked'):
        abort(400)

    user_service.toggle_status(user, new_status, current_user.id)
    flash(f'Status alterado para "{new_status}".', 'success')
    return redirect(url_for('users.detail', user_id=user.id))


@users_bp.route('/<int:user_id>/desbloquear', methods=['POST'])
@login_required
@admin_required
def unlock(user_id: int):
    user = db.session.get(User, user_id) or abort(404)
    user_service.unlock_user(user, current_user.id)
    flash('Usuário desbloqueado.', 'success')
    return redirect(url_for('users.detail', user_id=user.id))


@users_bp.route('/<int:user_id>/resetar-senha', methods=['POST'])
@login_required
@admin_required
def reset_password(user_id: int):
    user = db.session.get(User, user_id) or abort(404)
    user_service.reset_password_admin(user, current_user.id)
    flash(f'E-mail de redefinição de senha enviado para {user.email}.', 'info')
    return redirect(url_for('users.detail', user_id=user.id))


@users_bp.route('/<int:user_id>/definir-senha', methods=['GET', 'POST'])
@login_required
@admin_required
def set_password(user_id: int):
    user = db.session.get(User, user_id) or abort(404)
    if user.id == current_user.id:
        flash('Use a tela de perfil para alterar sua própria senha.', 'warning')
        return redirect(url_for('users.detail', user_id=user.id))

    form = AdminSetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        if form.force_change.data:
            user.first_login = True
        db.session.commit()
        flash(f'Senha de {user.name} atualizada com sucesso.', 'success')
        return redirect(url_for('users.detail', user_id=user.id))

    return render_template('users/set_password.html', form=form, user=user)


# ─── Departamentos ────────────────────────────────────────────────────────────

@users_bp.route('/departamentos/novo', methods=['POST'])
@login_required
@admin_required
def create_department():
    name = request.form.get('name', '').strip()
    if not name:
        flash('Nome do departamento não pode ser vazio.', 'warning')
    else:
        dept = user_service.create_department(name, current_user.id)
        flash(f'Departamento "{dept.name}" criado.', 'success')
    return redirect(request.referrer or url_for('users.index'))


# ─── IPs bloqueados ───────────────────────────────────────────────────────────

@users_bp.route('/ips-bloqueados')
@login_required
@admin_required
def blocked_ips():
    ips  = user_service.list_blocked_ips()
    form = BlockedIpForm()
    return render_template('users/blocked_ips.html', ips=ips, form=form)


@users_bp.route('/ips-bloqueados/bloquear', methods=['POST'])
@login_required
@admin_required
def block_ip():
    form = BlockedIpForm()
    if form.validate_on_submit():
        user_service.block_ip(form.ip_address.data.strip(),
                              form.reason.data or '', current_user.id)
        flash(f'IP {form.ip_address.data} bloqueado.', 'success')
    return redirect(url_for('users.blocked_ips'))


@users_bp.route('/ips-bloqueados/<int:ip_id>/desbloquear', methods=['POST'])
@login_required
@admin_required
def unblock_ip(ip_id: int):
    user_service.unblock_ip(ip_id, current_user.id)
    flash('IP desbloqueado.', 'success')
    return redirect(url_for('users.blocked_ips'))
