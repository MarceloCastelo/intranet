from datetime import datetime

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from app import db


class Department(db.Model):
    __tablename__ = 'departments'

    id         = db.Column(db.Integer, primary_key=True)
    name       = db.Column(db.String(100), nullable=False, unique=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    users       = db.relationship('User', back_populates='department', lazy='dynamic')
    permissions = db.relationship('Permission', back_populates='department',
                                  cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Department {self.name}>'


class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id              = db.Column(db.Integer, primary_key=True)
    name            = db.Column(db.String(150), nullable=False)
    email           = db.Column(db.String(150), nullable=False, unique=True)
    password_hash   = db.Column(db.String(255), nullable=False)
    role            = db.Column(db.Enum('admin', 'user', 'editor', 'viewer'), default='user')
    status          = db.Column(db.Enum('active', 'inactive', 'blocked'), default='active')
    profile_picture = db.Column(db.String(500))
    department_id   = db.Column(db.Integer, db.ForeignKey('departments.id', ondelete='SET NULL'))
    birth_date      = db.Column(db.Date)

    # 2FA
    two_factor_enabled    = db.Column(db.Boolean, default=False)
    two_factor_mandatory  = db.Column(db.Boolean, default=True)
    first_login           = db.Column(db.Boolean, default=True)

    # Segurança
    last_login_at  = db.Column(db.DateTime)
    last_login_ip  = db.Column(db.String(45))
    login_attempts = db.Column(db.Integer, default=0)
    locked_until   = db.Column(db.DateTime)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relacionamentos
    department       = db.relationship('Department', back_populates='users')
    permissions      = db.relationship('Permission', back_populates='user',
                                       foreign_keys='Permission.user_id',
                                       cascade='all, delete-orphan')
    password_history = db.relationship('PasswordHistory', back_populates='user',
                                       foreign_keys='PasswordHistory.user_id',
                                       cascade='all, delete-orphan')
    tokens           = db.relationship('UserToken', back_populates='user',
                                       cascade='all, delete-orphan')
    two_factor_logs  = db.relationship('TwoFactorLog', back_populates='user')
    sessions         = db.relationship('Session', back_populates='user',
                                       cascade='all, delete-orphan')

    __table_args__ = (
        db.Index('idx_users_status',     'status', 'role'),
        db.Index('idx_users_department', 'department_id', 'status'),
    )

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    @property
    def is_locked(self) -> bool:
        return bool(self.locked_until and self.locked_until > datetime.utcnow())

    def __repr__(self):
        return f'<User {self.email}>'


class PasswordHistory(db.Model):
    __tablename__ = 'password_history'

    id            = db.Column(db.Integer, primary_key=True)
    user_id       = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    changed_at    = db.Column(db.DateTime, default=datetime.utcnow)
    changed_by    = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'))

    user           = db.relationship('User', back_populates='password_history',
                                     foreign_keys=[user_id])
    changed_by_user = db.relationship('User', foreign_keys=[changed_by])

    __table_args__ = (
        db.Index('idx_password_history_user', 'user_id', 'changed_at'),
    )


class UserToken(db.Model):
    __tablename__ = 'user_tokens'

    id         = db.Column(db.Integer, primary_key=True)
    user_id    = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    token      = db.Column(db.String(255), nullable=False, unique=True)
    type       = db.Column(db.Enum('password_reset', 'invite', '2fa_email'), nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)
    used_at    = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', back_populates='tokens')

    __table_args__ = (
        db.Index('idx_user_tokens_user_type', 'user_id', 'type', 'used_at'),
    )


class TwoFactorLog(db.Model):
    __tablename__ = 'two_factor_logs'

    id             = db.Column(db.Integer, primary_key=True)
    user_id        = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'))
    success        = db.Column(db.Boolean, nullable=False)
    ip_address     = db.Column(db.String(45))
    user_agent     = db.Column(db.Text)
    failure_reason = db.Column(db.String(255))
    created_at     = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', back_populates='two_factor_logs')

    __table_args__ = (
        db.Index('idx_2fa_logs_user', 'user_id', 'created_at'),
        db.Index('idx_2fa_logs_ip',   'ip_address'),
    )


class Permission(db.Model):
    __tablename__ = 'permissions'

    id            = db.Column(db.Integer, primary_key=True)
    user_id       = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    resource      = db.Column(db.String(50), nullable=False)
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id', ondelete='CASCADE'))
    can_create    = db.Column(db.Boolean, default=False)
    can_edit      = db.Column(db.Boolean, default=False)
    can_delete    = db.Column(db.Boolean, default=False)
    can_publish   = db.Column(db.Boolean, default=False)
    created_at    = db.Column(db.DateTime, default=datetime.utcnow)

    user       = db.relationship('User', back_populates='permissions', foreign_keys=[user_id])
    department = db.relationship('Department', back_populates='permissions')

    __table_args__ = (
        db.Index('idx_permissions_user', 'user_id', 'resource'),
    )


class Session(db.Model):
    __tablename__ = 'sessions'

    id         = db.Column(db.Integer, primary_key=True)
    user_id    = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    token      = db.Column(db.String(255), nullable=False, unique=True)
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.Text)
    expires_at = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', back_populates='sessions')

    __table_args__ = (
        db.Index('idx_sessions_user', 'user_id', 'expires_at'),
    )
