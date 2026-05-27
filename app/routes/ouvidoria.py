from flask import (Blueprint, abort, flash, redirect,
                   render_template, request, url_for)
from flask_login import current_user, login_required

from app import db
from app.models.ouvidoria import Manifestacao, ManifestacaoResposta, OUVIDORIA_ROLES
from app.models.user import UnitState
from app.services.email_service import (notify_ouvidoria_nova_manifestacao,
                                        notify_ouvidoria_nova_resposta)
from app.utils.decorators import ouvidoria_required

ouvidoria_bp = Blueprint('ouvidoria', __name__, url_prefix='/ouvidoria')

# ── Rótulos ──────────────────────────────────────────────────────────────────

TIPO_LABELS = {
    'denuncia':   ('Denúncia',   'bg-red-100 text-red-700'),
    'reclamacao': ('Reclamação', 'bg-orange-100 text-orange-700'),
    'sugestao':   ('Sugestão',   'bg-blue-100 text-blue-700'),
}

STATUS_LABELS = {
    'pendente':     ('Pendente',      'bg-yellow-100 text-yellow-700'),
    'em_andamento': ('Em andamento',  'bg-blue-100 text-blue-700'),
    'concluida':    ('Concluída',     'bg-green-100 text-green-700'),
    'arquivada':    ('Arquivada',     'bg-gray-100 text-gray-500'),
}

# Rôles que NÃO podem ver denúncias (apenas reclamações e sugestões)
_RESTRICTED_ROLES = ('patrimonio', 'controladoria')


def _can_see_tipo(role: str, tipo: str) -> bool:
    """Retorna False se o perfil não tiver permissão para ver aquele tipo."""
    if role in _RESTRICTED_ROLES and tipo == 'denuncia':
        return False
    return True


# ── Rotas públicas ────────────────────────────────────────────────────────────

@ouvidoria_bp.route('/')
def index():
    """Formulário público de envio."""
    if current_user.is_authenticated:
        # Redireciona usuários com perfil de ouvidoria direto para o painel
        if current_user.role in OUVIDORIA_ROLES:
            return redirect(url_for('ouvidoria.admin_index'))
    states = UnitState.query.order_by(UnitState.name).all()
    return render_template('ouvidoria/index.html',
                           tipo_labels=TIPO_LABELS,
                           states=states)


@ouvidoria_bp.route('/enviar', methods=['POST'])
def enviar():
    """Processa o envio de uma nova manifestação."""
    tipo      = request.form.get('tipo', '').strip()
    assunto   = request.form.get('assunto', '').strip()
    descricao = request.form.get('descricao', '').strip()
    state_id  = request.form.get('state_id', '').strip()

    if tipo not in ('denuncia', 'reclamacao', 'sugestao'):
        flash('Tipo de manifestação inválido.', 'danger')
        return redirect(url_for('ouvidoria.index'))
    if not assunto or len(assunto) > 200:
        flash('Informe um assunto com até 200 caracteres.', 'danger')
        return redirect(url_for('ouvidoria.index'))
    if not descricao or len(descricao) < 20:
        flash('A descrição deve ter ao menos 20 caracteres.', 'danger')
        return redirect(url_for('ouvidoria.index'))
    if not state_id:
        flash('Selecione o estado da sua unidade.', 'danger')
        return redirect(url_for('ouvidoria.index'))

    # Valida que o estado existe
    state = db.session.get(UnitState, int(state_id)) if state_id.isdigit() else None
    if not state:
        flash('Estado inválido. Selecione um estado da lista.', 'danger')
        return redirect(url_for('ouvidoria.index'))

    m = Manifestacao(tipo=tipo, assunto=assunto, descricao=descricao, state_id=state.id)
    db.session.add(m)
    db.session.commit()

    # Notifica admins de denúncias do estado
    admin_url = url_for('ouvidoria.admin_detail', public_id=m.public_id, _external=True)
    notify_ouvidoria_nova_manifestacao(m, admin_url)

    return redirect(url_for('ouvidoria.confirmacao', public_id=m.public_id))


@ouvidoria_bp.route('/confirmacao/<public_id>')
def confirmacao(public_id: str):
    """Exibe o ID único gerado para acompanhamento."""
    m = Manifestacao.query.filter_by(public_id=public_id).first_or_404()
    tipo_info = TIPO_LABELS.get(m.tipo, (m.tipo, ''))
    return render_template('ouvidoria/confirmacao.html', m=m, tipo_info=tipo_info)


@ouvidoria_bp.route('/acompanhar', methods=['GET', 'POST'])
def acompanhar():
    """Interface de consulta e conversa pelo ID único."""
    # POST: redireciona para o GET com o ID na URL
    if request.method == 'POST':
        pid = request.form.get('public_id', '').strip().lower().replace('-', '').replace(' ', '')
        if pid:
            return redirect(url_for('ouvidoria.acompanhar', id=pid))
        return render_template('ouvidoria/acompanhar.html',
                               m=None, erro='Informe o ID da manifestação.',
                               tipo_info=None, status_info=None,
                               status_labels=STATUS_LABELS)

    # GET: carrega pelo ?id= ou mostra formulário vazio
    pid = request.args.get('id', '').strip().lower().replace('-', '').replace(' ', '')
    m = erro = tipo_info = status_info = None

    if pid:
        m = Manifestacao.query.filter_by(public_id=pid).first()
        if not m:
            erro = 'Nenhuma manifestação encontrada com esse ID.'
        else:
            tipo_info   = TIPO_LABELS.get(m.tipo, (m.tipo, ''))
            status_info = STATUS_LABELS.get(m.status, (m.status, ''))

    return render_template('ouvidoria/acompanhar.html',
                           m=m, erro=erro, pid=pid,
                           tipo_info=tipo_info,
                           status_info=status_info,
                           status_labels=STATUS_LABELS)


@ouvidoria_bp.route('/<public_id>/mensagem', methods=['POST'])
def autor_mensagem(public_id: str):
    """Mensagem enviada pelo autor anônimo via ID único."""
    m = Manifestacao.query.filter_by(public_id=public_id).first_or_404()

    if m.status in ('concluida', 'arquivada'):
        flash('Esta manifestação está encerrada e não aceita mais mensagens.', 'warning')
        return redirect(url_for('ouvidoria.acompanhar', id=public_id))

    conteudo = request.form.get('conteudo', '').strip()
    if not conteudo:
        flash('A mensagem não pode estar vazia.', 'danger')
        return redirect(url_for('ouvidoria.acompanhar', id=public_id))

    resposta = ManifestacaoResposta(
        manifestacao_id=m.id,
        respondente_id=None,
        conteudo=conteudo,
        origem='autor',
        status_anterior=m.status,
        status_novo=m.status,
    )
    # Reabre automaticamente se estava pendente → em_andamento quando autor responde
    if m.status == 'pendente':
        resposta.status_novo = 'em_andamento'
        m.status = 'em_andamento'

    db.session.add(resposta)
    db.session.commit()

    # Notifica admins de denúncias do estado sobre a nova resposta do autor
    admin_url = url_for('ouvidoria.admin_detail', public_id=m.public_id, _external=True)
    notify_ouvidoria_nova_resposta(m, admin_url)

    return redirect(url_for('ouvidoria.acompanhar', id=public_id))


# ── Rotas administrativas ─────────────────────────────────────────────────────

@ouvidoria_bp.route('/admin/')
@login_required
@ouvidoria_required
def admin_index():
    """Lista de manifestações filtrada pelo perfil do usuário logado."""
    page       = request.args.get('page', 1, type=int)
    tipo_f     = request.args.get('tipo', '').strip()
    status_f   = request.args.get('status', '').strip()
    state_f    = request.args.get('state_id', 0, type=int)
    role       = current_user.role

    q = Manifestacao.query.order_by(Manifestacao.created_at.desc())

    # patrimônio não vê denúncias
    if role in _RESTRICTED_ROLES:
        q = q.filter(Manifestacao.tipo.in_(['reclamacao', 'sugestao']))

    # RH vê apenas manifestações do seu estado (sempre, independente de is_admin)
    # exceto quando ouvidoria_all_states=True
    if role == 'rh' and not current_user.ouvidoria_all_states:
        if current_user.state_id:
            q = q.filter(Manifestacao.state_id == current_user.state_id)
        else:
            # RH sem estado configurado não vê nenhuma manifestação
            q = q.filter(db.false())

    if tipo_f and _can_see_tipo(role, tipo_f):
        q = q.filter(Manifestacao.tipo == tipo_f)
    elif tipo_f and not _can_see_tipo(role, tipo_f):
        tipo_f = ''  # ignora filtro não permitido

    if status_f:
        q = q.filter(Manifestacao.status == status_f)

    # Filtro manual por estado (para admins ou RH com acesso total)
    can_filter_state = (current_user.is_admin and role != 'rh') or \
                       (role == 'rh' and current_user.ouvidoria_all_states)
    if can_filter_state and state_f:
        q = q.filter(Manifestacao.state_id == state_f)

    pagination = q.paginate(page=page, per_page=40, error_out=False)
    all_states = UnitState.query.order_by(UnitState.name).all() if can_filter_state else []

    return render_template(
        'ouvidoria/admin/index.html',
        pagination=pagination,
        tipo_f=tipo_f,
        status_f=status_f,
        state_f=state_f,
        tipo_labels=TIPO_LABELS,
        status_labels=STATUS_LABELS,
        can_see_denuncia=_can_see_tipo(role, 'denuncia'),
        all_states=all_states,
    )


@ouvidoria_bp.route('/admin/<public_id>')
@login_required
@ouvidoria_required
def admin_detail(public_id: str):
    """Detalhe de uma manifestação e histórico de respostas."""
    m    = Manifestacao.query.filter_by(public_id=public_id).first_or_404()
    role = current_user.role

    # Patrimônio não acessa denúncias mesmo pela URL direta
    if not _can_see_tipo(role, m.tipo):
        abort(403)

    # RH só acessa manifestações do seu estado (sempre, independente de is_admin)
    if role == 'rh' and not current_user.ouvidoria_all_states:
        if not current_user.state_id or m.state_id != current_user.state_id:
            abort(403)

    tipo_info   = TIPO_LABELS.get(m.tipo, (m.tipo, ''))
    status_info = STATUS_LABELS.get(m.status, (m.status, ''))

    return render_template(
        'ouvidoria/admin/detail.html',
        m=m,
        tipo_info=tipo_info,
        status_info=status_info,
        status_labels=STATUS_LABELS,
    )


@ouvidoria_bp.route('/admin/<public_id>/responder', methods=['POST'])
@login_required
@ouvidoria_required
def admin_responder(public_id: str):
    """Registra uma resposta e opcionalmente muda o status."""
    m    = Manifestacao.query.filter_by(public_id=public_id).first_or_404()
    role = current_user.role

    if not _can_see_tipo(role, m.tipo):
        abort(403)

    # RH só responde manifestações do seu estado (sempre, independente de is_admin)
    if role == 'rh' and not current_user.ouvidoria_all_states:
        if not current_user.state_id or m.state_id != current_user.state_id:
            abort(403)

    conteudo   = request.form.get('conteudo', '').strip()
    status_novo = request.form.get('status_novo', m.status).strip()

    if not conteudo:
        flash('O conteúdo da resposta não pode estar vazio.', 'danger')
        return redirect(url_for('ouvidoria.admin_detail', public_id=public_id))

    if status_novo not in STATUS_LABELS:
        status_novo = m.status

    resposta = ManifestacaoResposta(
        manifestacao_id=m.id,
        respondente_id=current_user.id,
        conteudo=conteudo,
        origem='responsavel',
        status_anterior=m.status,
        status_novo=status_novo,
    )
    m.status = status_novo

    db.session.add(resposta)
    db.session.commit()

    flash('Resposta registrada com sucesso.', 'success')
    return redirect(url_for('ouvidoria.admin_detail', public_id=public_id))


@ouvidoria_bp.route('/admin/<public_id>/excluir', methods=['POST'])
@login_required
@ouvidoria_required
def admin_excluir(public_id: str):
    """Exclui permanentemente uma manifestação. Apenas is_admin ou role='rh'."""
    if not (current_user.is_admin or current_user.role == 'rh'):
        abort(403)

    m = Manifestacao.query.filter_by(public_id=public_id).first_or_404()

    # RH sem acesso a todos os estados só pode excluir do seu estado
    if current_user.role == 'rh' and not current_user.ouvidoria_all_states:
        if not current_user.state_id or m.state_id != current_user.state_id:
            abort(403)

    db.session.delete(m)
    db.session.commit()
    flash('Manifestação excluída permanentemente.', 'success')
    return redirect(url_for('ouvidoria.admin_index'))
