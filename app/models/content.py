from datetime import datetime

from app import db


class Banner(db.Model):
    __tablename__ = 'banners'

    id             = db.Column(db.Integer, primary_key=True)
    title          = db.Column(db.String(100))
    description    = db.Column(db.Text)
    image_path     = db.Column(db.String(500), nullable=False)
    link_url       = db.Column(db.String(500))
    link_text      = db.Column(db.String(50))
    order_position = db.Column(db.Integer, default=0)
    is_active      = db.Column(db.Boolean, default=True)
    start_date     = db.Column(db.Date)
    end_date       = db.Column(db.Date)
    target_blank   = db.Column(db.Boolean, default=True)
    created_by     = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'))
    created_at     = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at     = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    creator = db.relationship('User', foreign_keys=[created_by])

    __table_args__ = (
        db.Index('idx_banners_active', 'is_active', 'start_date', 'end_date'),
        db.Index('idx_banners_order',  'order_position'),
    )


class FaqCategory(db.Model):
    __tablename__ = 'faq_categories'

    id             = db.Column(db.Integer, primary_key=True)
    name           = db.Column(db.String(100), nullable=False)
    description    = db.Column(db.Text)
    order_position = db.Column(db.Integer, default=0)
    is_active      = db.Column(db.Boolean, default=True)
    created_at     = db.Column(db.DateTime, default=datetime.utcnow)

    faqs = db.relationship('Faq', back_populates='category')


class Faq(db.Model):
    __tablename__ = 'faq'

    id                = db.Column(db.Integer, primary_key=True)
    category_id       = db.Column(db.Integer, db.ForeignKey('faq_categories.id', ondelete='SET NULL'))
    question          = db.Column(db.String(255), nullable=False)
    answer            = db.Column(db.Text, nullable=False)
    order_position    = db.Column(db.Integer, default=0)
    is_active         = db.Column(db.Boolean, default=True)
    views_count       = db.Column(db.Integer, default=0)
    helpful_count     = db.Column(db.Integer, default=0)
    not_helpful_count = db.Column(db.Integer, default=0)
    created_by        = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'))
    created_at        = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at        = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    category = db.relationship('FaqCategory', back_populates='faqs')
    creator  = db.relationship('User', foreign_keys=[created_by])

    __table_args__ = (
        db.Index('idx_faq_active', 'is_active', 'order_position'),
    )


class Poll(db.Model):
    __tablename__ = 'polls'

    id          = db.Column(db.Integer, primary_key=True)
    question    = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    is_active   = db.Column(db.Boolean, default=True)
    is_multiple = db.Column(db.Boolean, default=False)
    created_by  = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'))
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at  = db.Column(db.DateTime)

    creator = db.relationship('User', foreign_keys=[created_by])
    options = db.relationship('PollOption', back_populates='poll', cascade='all, delete-orphan')
    votes   = db.relationship('PollVote',   back_populates='poll')

    __table_args__ = (
        db.Index('idx_polls_active',  'is_active', 'expires_at'),
        db.Index('idx_polls_expires', 'is_active', 'expires_at'),
    )


class PollOption(db.Model):
    __tablename__ = 'poll_options'

    id             = db.Column(db.Integer, primary_key=True)
    poll_id        = db.Column(db.Integer, db.ForeignKey('polls.id', ondelete='CASCADE'), nullable=False)
    option_text    = db.Column(db.String(255), nullable=False)
    order_position = db.Column(db.Integer, default=0)

    poll  = db.relationship('Poll', back_populates='options')
    votes = db.relationship('PollVote', back_populates='option')

    __table_args__ = (
        db.Index('idx_poll_options_poll', 'poll_id'),
    )


class PollVote(db.Model):
    __tablename__ = 'poll_votes'

    id        = db.Column(db.Integer, primary_key=True)
    poll_id   = db.Column(db.Integer, db.ForeignKey('polls.id',        ondelete='RESTRICT'), nullable=False)
    option_id = db.Column(db.Integer, db.ForeignKey('poll_options.id', ondelete='RESTRICT'), nullable=False)
    user_id   = db.Column(db.Integer, db.ForeignKey('users.id',        ondelete='RESTRICT'), nullable=False)
    voted_at  = db.Column(db.DateTime, default=datetime.utcnow)

    poll   = db.relationship('Poll',       back_populates='votes')
    option = db.relationship('PollOption', back_populates='votes')
    user   = db.relationship('User', foreign_keys=[user_id])

    __table_args__ = (
        db.UniqueConstraint('user_id', 'poll_id', name='uq_user_poll'),
        db.Index('idx_poll_votes_option', 'option_id'),
    )


class Gallery(db.Model):
    __tablename__ = 'galleries'

    id          = db.Column(db.Integer, primary_key=True)
    title       = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    cover_image = db.Column(db.String(500))
    created_by  = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'))
    is_active   = db.Column(db.Boolean, default=True)
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at  = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    creator = db.relationship('User', foreign_keys=[created_by])
    items   = db.relationship('GalleryItem', back_populates='gallery', cascade='all, delete-orphan')

    __table_args__ = (
        db.Index('idx_galleries_active', 'is_active'),
    )


class GalleryItem(db.Model):
    __tablename__ = 'gallery_items'

    id             = db.Column(db.Integer, primary_key=True)
    gallery_id     = db.Column(db.Integer, db.ForeignKey('galleries.id', ondelete='CASCADE'), nullable=False)
    image_path     = db.Column(db.String(500), nullable=False)
    thumbnail_path = db.Column(db.String(500))
    caption        = db.Column(db.String(255))
    order_position = db.Column(db.Integer, default=0)

    gallery = db.relationship('Gallery', back_populates='items')

    __table_args__ = (
        db.Index('idx_gallery_items_order', 'gallery_id', 'order_position'),
    )


class ContentVersion(db.Model):
    __tablename__ = 'content_versions'

    id             = db.Column(db.Integer, primary_key=True)
    entity         = db.Column(db.String(50), nullable=False)   # 'news' | 'page'
    entity_id      = db.Column(db.Integer,    nullable=False)
    content_json   = db.Column(db.JSON)
    version_number = db.Column(db.Integer, nullable=False)
    created_by     = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'))
    created_at     = db.Column(db.DateTime, default=datetime.utcnow)

    creator = db.relationship('User', foreign_keys=[created_by])

    __table_args__ = (
        db.UniqueConstraint('entity', 'entity_id', 'version_number', name='uq_entity_version'),
        db.Index('idx_cv_entity', 'entity', 'entity_id', 'created_at'),
    )
