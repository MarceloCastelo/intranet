from flask import (Blueprint, abort, flash, redirect,
                   render_template, request, url_for)
from flask_login import current_user, login_required

from app import db
from app.forms.user import AdminSetPasswordForm, InviteUserForm, ProfileForm, UserForm
from app.models.user import User
from app.services import user_service
from app.utils.decorators import admin_required

users_bp = Blueprint('users', __name__, url_prefix='/admin/usuarios')


# ─── Perfil do usuário logado ─────────────────────────────────────────────────

@users_bp.route('/perfil', methods=['GET', 'POST'])
@login_required
def profile():
    form = ProfileForm(user_id=current_user.id, obj=current_user)
    if form.validate_on_submit():
        current_user.name       = form.name.data.strip()
        current_user.email      = form.email.data.strip().lower()
        current_user.birth_date = form.birth_date.data
        if form.profile_picture.data and form.profile_picture.data.filename:
            current_user.profile_picture = user_service.save_profile_picture(
                form.profile_picture.data, current_user.profile_picture
            )
        db.session.commit()
        flash('Perfil atualizado com sucesso.', 'success')
        return redirect(url_for('users.profile'))
    return render_template('users/profile.html', form=form)

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
    form = UserForm(departments=departments, states=user_service.all_states())

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
    form = InviteUserForm(departments=departments, states=user_service.all_states())

    if form.validate_on_submit():
        try:
            user = user_service.invite_user(form, current_user.id)
            flash(f'Convite enviado para {user.email}.', 'success')
            return redirect(url_for('users.index'))
        except ValueError as exc:
            form.email.errors.append(str(exc))
        except RuntimeError as exc:
            flash(str(exc), 'danger')

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
    form = UserForm(departments=departments, states=user_service.all_states(), user_id=user.id, obj=user)

    # Pré-popula department_id no GET
    if request.method == 'GET':
        form.department_id.data = user.department_id or 0
        form.state_id.data      = user.state_id or 0

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
    form = AdminSetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        user.first_login = bool(form.force_change.data)
        from app.models.audit import AuditLog
        db.session.add(AuditLog(
            user_id=current_user.id, action='update',
            entity='users', entity_id=user.id,
            new_values={'action': 'admin_set_password'},
        ))
        db.session.commit()
        flash(f'Senha de {user.name} atualizada com sucesso.', 'success')
        return redirect(url_for('users.detail', user_id=user.id))

    return render_template('users/set_password.html', form=form, user=user)


# ─── Departamentos ────────────────────────────────────────────────────────────

@users_bp.route('/<int:user_id>/excluir', methods=['POST'])
@login_required
@admin_required
def delete(user_id: int):
    user = db.session.get(User, user_id) or abort(404)
    name = user.name
    is_self = user.id == current_user.id
    db.session.delete(user)
    db.session.commit()
    flash(f'Usuário "{name}" excluído permanentemente.', 'success')
    if is_self:
        from flask_login import logout_user
        logout_user()
        return redirect(url_for('auth.login'))
    return redirect(url_for('users.index'))


# ─── Departamentos ────────────────────────────────────────────────────────────

@users_bp.route('/departamentos')
@login_required
@admin_required
def departments():
    depts = user_service.all_departments()
    return render_template('users/departments.html', departments=depts)


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
    return redirect(url_for('users.departments'))


@users_bp.route('/departamentos/<int:dept_id>/editar', methods=['POST'])
@login_required
@admin_required
def edit_department(dept_id: int):
    from app.models.user import Department
    dept = db.session.get(Department, dept_id) or abort(404)
    name = request.form.get('name', '').strip()
    if not name:
        flash('Nome não pode ser vazio.', 'warning')
    else:
        dept.name = name
        db.session.commit()
        flash(f'Departamento renomeado para "{name}".', 'success')
    return redirect(url_for('users.departments'))


@users_bp.route('/departamentos/<int:dept_id>/excluir', methods=['POST'])
@login_required
@admin_required
def delete_department(dept_id: int):
    from app.models.user import Department
    dept = db.session.get(Department, dept_id) or abort(404)
    if dept.users.count() > 0:
        flash(f'Não é possível excluir "{dept.name}": há usuários vinculados.', 'warning')
        return redirect(url_for('users.departments'))
    name = dept.name
    db.session.delete(dept)
    db.session.commit()
    flash(f'Departamento "{name}" excluído.', 'success')
    return redirect(url_for('users.departments'))


# ─── Estados ──────────────────────────────────────────────────────────────────

@users_bp.route('/estados')
@login_required
@admin_required
def states():
    unit_states = user_service.all_states()
    return render_template('users/states.html', states=unit_states)


@users_bp.route('/estados/novo', methods=['POST'])
@login_required
@admin_required
def create_state():
    name = request.form.get('name', '').strip()
    if not name:
        flash('Nome do estado não pode ser vazio.', 'warning')
    else:
        state = user_service.create_state(name, current_user.id)
        flash(f'Estado "{state.name}" criado.', 'success')
    return redirect(url_for('users.states'))


@users_bp.route('/estados/<int:state_id>/editar', methods=['POST'])
@login_required
@admin_required
def edit_state(state_id: int):
    from app.models.user import UnitState
    state = db.session.get(UnitState, state_id) or abort(404)
    name = request.form.get('name', '').strip()
    if not name:
        flash('Nome não pode ser vazio.', 'warning')
    else:
        state.name = name
        db.session.commit()
        flash(f'Estado renomeado para "{name}".', 'success')
    return redirect(url_for('users.states'))


@users_bp.route('/estados/<int:state_id>/excluir', methods=['POST'])
@login_required
@admin_required
def delete_state(state_id: int):
    from app.models.user import UnitState
    state = db.session.get(UnitState, state_id) or abort(404)
    if state.users.count() > 0:
        flash(f'Não é possível excluir "{state.name}": há usuários vinculados.', 'warning')
        return redirect(url_for('users.states'))
    name = state.name
    db.session.delete(state)
    db.session.commit()
    flash(f'Estado "{name}" excluído.', 'success')
    return redirect(url_for('users.states'))

