from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app.forms.content import FaqCategoryForm, FaqForm
from app.services.content_service import (all_faq_categories, create_faq,
                                           create_faq_category, delete_faq,
                                           delete_faq_category,
                                           get_faq_category_or_404,
                                           get_faq_or_404, update_faq,
                                           update_faq_category)
from app.utils.decorators import editor_or_admin_required

faq_bp = Blueprint('faq', __name__, url_prefix='/faq')


def _set_category_choices(form):
    cats = all_faq_categories()
    form.category_id.choices = [(0, '— Sem categoria —')] + [(c.id, c.name) for c in cats]
    return cats


# ── Categorias ────────────────────────────────────────────────────────────────

@faq_bp.route('/admin/categorias')
@login_required
@editor_or_admin_required
def categories():
    cats = all_faq_categories()
    form = FaqCategoryForm()
    return render_template('faq/categories.html', categories=cats, form=form)


@faq_bp.route('/admin/categorias/criar', methods=['POST'])
@login_required
@editor_or_admin_required
def create_category():
    form = FaqCategoryForm()
    if form.validate_on_submit():
        create_faq_category(form)
        flash('Categoria criada.', 'success')
    return redirect(url_for('faq.categories'))


@faq_bp.route('/admin/categorias/<int:cat_id>/editar', methods=['GET', 'POST'])
@login_required
@editor_or_admin_required
def edit_category(cat_id):
    cat  = get_faq_category_or_404(cat_id)
    form = FaqCategoryForm(obj=cat)
    if form.validate_on_submit():
        update_faq_category(cat, form)
        flash('Categoria atualizada.', 'success')
        return redirect(url_for('faq.categories'))
    return render_template('faq/category_form.html', form=form, cat=cat)


@faq_bp.route('/admin/categorias/<int:cat_id>/excluir', methods=['POST'])
@login_required
@editor_or_admin_required
def delete_category(cat_id):
    cat = get_faq_category_or_404(cat_id)
    delete_faq_category(cat)
    flash('Categoria excluída.', 'success')
    return redirect(url_for('faq.categories'))


# ── FAQs ──────────────────────────────────────────────────────────────────────

@faq_bp.route('/')
@login_required
def public_list():
    cats = all_faq_categories()
    return render_template('faq/public_list.html', categories=cats)


@faq_bp.route('/admin')
@login_required
@editor_or_admin_required
def index():
    cats = all_faq_categories()
    return render_template('faq/index.html', categories=cats)


@faq_bp.route('/admin/criar', methods=['GET', 'POST'])
@login_required
@editor_or_admin_required
def create():
    form = FaqForm()
    _set_category_choices(form)
    if form.validate_on_submit():
        faq = create_faq(form, actor_id=current_user.id)
        flash('FAQ criada.', 'success')
        return redirect(url_for('faq.index'))
    return render_template('faq/form.html', form=form, title='Nova FAQ', faq=None)


@faq_bp.route('/admin/<int:faq_id>/editar', methods=['GET', 'POST'])
@login_required
@editor_or_admin_required
def edit(faq_id):
    faq  = get_faq_or_404(faq_id)
    form = FaqForm(obj=faq)
    _set_category_choices(form)
    if form.validate_on_submit():
        update_faq(faq, form)
        flash('FAQ atualizada.', 'success')
        return redirect(url_for('faq.index'))
    return render_template('faq/form.html', form=form, title='Editar FAQ', faq=faq)


@faq_bp.route('/admin/<int:faq_id>/excluir', methods=['POST'])
@login_required
@editor_or_admin_required
def delete(faq_id):
    faq = get_faq_or_404(faq_id)
    delete_faq(faq)
    flash('FAQ excluída.', 'success')
    return redirect(url_for('faq.index'))
