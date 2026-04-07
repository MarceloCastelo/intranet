from datetime import datetime

from app import db


class Event(db.Model):
    __tablename__ = 'events'

    id              = db.Column(db.Integer, primary_key=True)
    title           = db.Column(db.String(255), nullable=False)
    description     = db.Column(db.JSON)
    event_date      = db.Column(db.Date, nullable=False)
    event_time      = db.Column(db.Time)
    end_date        = db.Column(db.Date)
    location        = db.Column(db.String(255))
    location_url    = db.Column(db.String(500))
    created_by      = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'))
    event_type      = db.Column(
        db.Enum('general', 'birthday', 'meeting', 'training', 'holiday'),
        default='general',
    )
    related_user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'))
    is_active       = db.Column(db.Boolean, default=True)
    created_at      = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at      = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    creator      = db.relationship('User', foreign_keys=[created_by])
    related_user = db.relationship('User', foreign_keys=[related_user_id])

    __table_args__ = (
        db.Index('idx_events_date',     'event_date', 'is_active'),
        db.Index('idx_events_type',     'event_type'),
        db.Index('idx_events_upcoming', 'event_date', 'is_active'),
    )

    def __repr__(self):
        return f'<Event {self.title} {self.event_date}>'
