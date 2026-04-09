import uuid
from datetime import datetime

from app import db


# Roles que têm acesso ao painel de ouvidoria (além de is_admin)
OUVIDORIA_ROLES = ('rh', 'patrimonio', 'controladoria')


def _gen_public_id() -> str:
    return uuid.uuid4().hex  # 32 hex chars, non-sequential


class Manifestacao(db.Model):
    __tablename__ = 'manifestacoes'

    id         = db.Column(db.Integer, primary_key=True)
    public_id  = db.Column(db.String(32), nullable=False, unique=True, default=_gen_public_id, index=True)
    tipo       = db.Column(db.Enum('denuncia', 'reclamacao', 'sugestao'), nullable=False)
    assunto    = db.Column(db.String(200), nullable=False)
    descricao  = db.Column(db.Text, nullable=False)
    status     = db.Column(
        db.Enum('pendente', 'em_andamento', 'concluida', 'arquivada'),
        nullable=False, default='pendente'
    )
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Sem colunas de identificação do autor — anonimato garantido

    respostas = db.relationship(
        'ManifestacaoResposta',
        back_populates='manifestacao',
        cascade='all, delete-orphan',
        order_by='ManifestacaoResposta.created_at',
    )

    def __repr__(self):
        return f'<Manifestacao {self.public_id} [{self.tipo}] {self.status}>'


class ManifestacaoResposta(db.Model):
    __tablename__ = 'manifestacao_respostas'

    id               = db.Column(db.Integer, primary_key=True)
    manifestacao_id  = db.Column(db.Integer, db.ForeignKey('manifestacoes.id', ondelete='CASCADE'), nullable=False)
    respondente_id   = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    conteudo         = db.Column(db.Text, nullable=False)
    origem           = db.Column(db.Enum('responsavel', 'autor'), nullable=False, default='responsavel')
    status_anterior  = db.Column(db.String(20), nullable=False)
    status_novo      = db.Column(db.String(20), nullable=False)
    created_at       = db.Column(db.DateTime, default=datetime.utcnow)

    manifestacao = db.relationship('Manifestacao', back_populates='respostas')
    respondente  = db.relationship('User', foreign_keys=[respondente_id])

    def __repr__(self):
        return f'<ManifestacaoResposta {self.id} -> manifestacao {self.manifestacao_id}>'
