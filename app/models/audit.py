from datetime import datetime

from app import db


class Favorite(db.Model):
    __tablename__ = 'favorites'

    id         = db.Column(db.Integer, primary_key=True)
    user_id    = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    entity     = db.Column(db.String(50), nullable=False)   # 'news' | 'link' | 'event' | 'faq'
    entity_id  = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', foreign_keys=[user_id])

    __table_args__ = (
        db.UniqueConstraint('user_id', 'entity', 'entity_id', name='uq_user_favorite'),
        db.Index('idx_favorites_user', 'user_id', 'created_at'),
    )


class ApprovalWorkflow(db.Model):
    __tablename__ = 'approval_workflow'

    id           = db.Column(db.Integer, primary_key=True)
    entity       = db.Column(db.String(50), nullable=False)   # 'news' | 'page'
    entity_id    = db.Column(db.Integer, nullable=False)
    requested_by = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='RESTRICT'))
    approved_by  = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='RESTRICT'))
    status       = db.Column(db.Enum('pending', 'approved', 'rejected', 'revised'), default='pending')
    comments     = db.Column(db.Text)
    requested_at = db.Column(db.DateTime, default=datetime.utcnow)
    approved_at  = db.Column(db.DateTime)

    requester = db.relationship('User', foreign_keys=[requested_by])
    approver  = db.relationship('User', foreign_keys=[approved_by])

    __table_args__ = (
        db.Index('idx_approval_entity',  'entity', 'entity_id', 'status'),
        db.Index('idx_approval_pending', 'status', 'requested_at'),
    )


class Notification(db.Model):
    __tablename__ = 'notifications'

    id         = db.Column(db.Integer, primary_key=True)
    user_id    = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    type       = db.Column(db.String(50),  nullable=False)   # 'news_published' | 'approval_pending' | …
    message    = db.Column(db.String(500), nullable=False)
    entity     = db.Column(db.String(50))
    entity_id  = db.Column(db.Integer)
    read_at    = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', foreign_keys=[user_id])

    __table_args__ = (
        db.Index('idx_notifications_user', 'user_id', 'read_at', 'created_at'),
    )


class AuditLog(db.Model):
    __tablename__ = 'audit_logs'

    id         = db.Column(db.Integer, primary_key=True)
    user_id    = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'))
    action     = db.Column(db.String(50))   # 'create' | 'update' | 'delete' | 'publish' | 'approve'
    entity     = db.Column(db.String(50))
    entity_id  = db.Column(db.Integer)
    old_values = db.Column(db.JSON)
    new_values = db.Column(db.JSON)
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', foreign_keys=[user_id])

    __table_args__ = (
        db.Index('idx_audit_entity', 'entity', 'entity_id', 'created_at'),
        db.Index('idx_audit_user',   'user_id', 'created_at'),
        db.Index('idx_audit_action', 'action',  'created_at'),
    )
