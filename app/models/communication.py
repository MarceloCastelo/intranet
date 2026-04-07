from datetime import datetime

from app import db


class PhoneExtension(db.Model):
    __tablename__ = 'phone_extensions'

    id             = db.Column(db.Integer, primary_key=True)
    name           = db.Column(db.String(150), nullable=False)   # pessoa ou setor
    extension      = db.Column(db.String(20),  nullable=False)   # número do ramal
    department_id  = db.Column(db.Integer, db.ForeignKey('departments.id', ondelete='SET NULL'))
    user_id        = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'))
    notes          = db.Column(db.String(255))
    order_position = db.Column(db.Integer, default=0)
    is_active      = db.Column(db.Boolean, default=True)
    created_by     = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'))
    created_at     = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at     = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    department = db.relationship('Department', foreign_keys=[department_id])
    user       = db.relationship('User', foreign_keys=[user_id])
    creator    = db.relationship('User', foreign_keys=[created_by])

    __table_args__ = (
        db.Index('idx_extensions_active', 'is_active', 'order_position'),
    )


class Service(db.Model):
    """Links de serviços/ferramentas da empresa (e-mail, TI, RH, etc.)."""
    __tablename__ = 'services'

    id             = db.Column(db.Integer, primary_key=True)
    title          = db.Column(db.String(150), nullable=False)
    url            = db.Column(db.String(500), nullable=False)
    description    = db.Column(db.String(255))
    category       = db.Column(db.String(100), default='Geral')   # agrupamento
    color          = db.Column(db.String(30),  default='blue')    # paleta de cores
    icon_url       = db.Column(db.String(500))                     # logo/ícone opcional
    target_blank   = db.Column(db.Boolean, default=True)
    order_position = db.Column(db.Integer, default=0)
    is_active      = db.Column(db.Boolean, default=True)
    created_by     = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'))
    created_at     = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at     = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    creator = db.relationship('User', foreign_keys=[created_by])

    __table_args__ = (
        db.Index('idx_services_active', 'is_active', 'category', 'order_position'),
    )


class Link(db.Model):
    __tablename__ = 'links'

    id             = db.Column(db.Integer, primary_key=True)
    title          = db.Column(db.String(150), nullable=False)
    url            = db.Column(db.String(500), nullable=False)
    description    = db.Column(db.String(255))
    icon_class     = db.Column(db.String(50))
    target_blank   = db.Column(db.Boolean, default=True)
    order_position = db.Column(db.Integer, default=0)
    is_active      = db.Column(db.Boolean, default=True)
    created_by     = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'))
    created_at     = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at     = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    creator = db.relationship('User', foreign_keys=[created_by])

    __table_args__ = (
        db.Index('idx_links_active', 'is_active', 'order_position'),
    )


class File(db.Model):
    __tablename__ = 'files'

    id                 = db.Column(db.Integer, primary_key=True)
    file_name          = db.Column(db.String(255), nullable=False)
    file_original_name = db.Column(db.String(255), nullable=False)
    file_path          = db.Column(db.String(500), nullable=False)
    file_size          = db.Column(db.Integer)    # bytes
    file_type          = db.Column(db.String(50))  # MIME type
    entity             = db.Column(db.String(50))  # 'news' | 'pages' | 'banners' | NULL
    entity_id          = db.Column(db.Integer)
    uploaded_by        = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'))
    created_at         = db.Column(db.DateTime, default=datetime.utcnow)

    uploader = db.relationship('User', foreign_keys=[uploaded_by])

    __table_args__ = (
        db.Index('idx_files_entity',   'entity', 'entity_id'),
        db.Index('idx_files_uploader', 'uploaded_by'),
    )


class Subscriber(db.Model):
    __tablename__ = 'subscribers'

    id                = db.Column(db.Integer, primary_key=True)
    email             = db.Column(db.String(150), nullable=False, unique=True)
    name              = db.Column(db.String(150))
    is_active         = db.Column(db.Boolean, default=True)
    subscribed_at     = db.Column(db.DateTime, default=datetime.utcnow)
    unsubscribed_at   = db.Column(db.DateTime)
    unsubscribe_token = db.Column(db.String(255))

    logs = db.relationship('NewsletterLog', back_populates='subscriber')

    __table_args__ = (
        db.Index('idx_subscribers_active', 'is_active', 'subscribed_at'),
    )


class Newsletter(db.Model):
    __tablename__ = 'newsletters'

    id           = db.Column(db.Integer, primary_key=True)
    subject      = db.Column(db.String(255), nullable=False)
    content      = db.Column(db.JSON, nullable=False)
    status       = db.Column(db.Enum('draft', 'sent', 'failed'), default='draft')
    sent_at      = db.Column(db.DateTime)
    total_sent   = db.Column(db.Integer, default=0)
    total_opened = db.Column(db.Integer, default=0)
    created_by   = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'))
    created_at   = db.Column(db.DateTime, default=datetime.utcnow)

    creator = db.relationship('User', foreign_keys=[created_by])
    logs    = db.relationship('NewsletterLog', back_populates='newsletter',
                              cascade='all, delete-orphan')

    __table_args__ = (
        db.Index('idx_newsletters_status', 'status', 'sent_at'),
    )


class NewsletterLog(db.Model):
    __tablename__ = 'newsletter_logs'

    id            = db.Column(db.Integer, primary_key=True)
    newsletter_id = db.Column(db.Integer, db.ForeignKey('newsletters.id', ondelete='CASCADE'), nullable=False)
    subscriber_id = db.Column(db.Integer, db.ForeignKey('subscribers.id', ondelete='RESTRICT'),  nullable=False)
    status        = db.Column(db.Enum('sent', 'opened', 'failed'), default='sent')
    sent_at       = db.Column(db.DateTime, default=datetime.utcnow)
    opened_at     = db.Column(db.DateTime)
    error_message = db.Column(db.Text)

    newsletter = db.relationship('Newsletter',  back_populates='logs')
    subscriber = db.relationship('Subscriber',  back_populates='logs')

    __table_args__ = (
        db.Index('idx_newsletter_logs', 'newsletter_id', 'status'),
    )


class EmailLog(db.Model):
    __tablename__ = 'email_logs'

    id            = db.Column(db.Integer, primary_key=True)
    recipient     = db.Column(db.String(150), nullable=False)
    subject       = db.Column(db.String(255), nullable=False)
    type          = db.Column(db.String(50))   # '2fa' | 'password_reset' | 'invite' | 'newsletter'
    status        = db.Column(db.Enum('sent', 'failed', 'opened'), default='sent')
    error_message = db.Column(db.Text)
    sent_at       = db.Column(db.DateTime, default=datetime.utcnow)
    opened_at     = db.Column(db.DateTime)

    __table_args__ = (
        db.Index('idx_email_logs_recipient', 'recipient', 'sent_at'),
        db.Index('idx_email_logs_type',      'type',      'sent_at'),
    )
