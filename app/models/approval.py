from datetime import datetime

from app import db


class ContentApproval(db.Model):
    """Fila de aprovações para ações de editores sobre conteúdo publicado."""
    __tablename__ = 'content_approvals'

    id               = db.Column(db.Integer, primary_key=True)
    action           = db.Column(db.Enum('publish', 'unpublish', 'edit', 'delete'), nullable=False)
    content_type     = db.Column(db.Enum('news', 'page'), nullable=False)
    content_id       = db.Column(db.Integer, nullable=False)

    # Quem solicitou
    requested_by_id  = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    requested_at     = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # Status
    status           = db.Column(db.Enum('pending', 'approved', 'rejected'), nullable=False, default='pending')

    # Revisão
    reviewed_by_id   = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    reviewed_at      = db.Column(db.DateTime, nullable=True)
    review_note      = db.Column(db.Text, nullable=True)

    # Para ação 'edit': guarda o snapshot serializado da nova versão a aplicar
    snapshot         = db.Column(db.JSON, nullable=True)

    # Título/nome do conteúdo no momento da solicitação (para exibição na fila)
    content_title    = db.Column(db.String(255), nullable=True)

    requested_by = db.relationship('User', foreign_keys=[requested_by_id])
    reviewed_by  = db.relationship('User', foreign_keys=[reviewed_by_id])

    __table_args__ = (
        db.Index('idx_approvals_status',   'status', 'requested_at'),
        db.Index('idx_approvals_content',  'content_type', 'content_id'),
    )

    def __repr__(self):
        return f'<ContentApproval {self.id} [{self.action}:{self.content_type}:{self.content_id}] {self.status}>'
