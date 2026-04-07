from datetime import datetime

from app import db

# ─── Tabelas de junção N:N ────────────────────────────────────────────────────

news_categories = db.Table(
    'news_categories',
    db.Column('news_id',     db.Integer, db.ForeignKey('news.id',       ondelete='CASCADE'), primary_key=True),
    db.Column('category_id', db.Integer, db.ForeignKey('categories.id', ondelete='CASCADE'), primary_key=True),
)

news_tags = db.Table(
    'news_tags',
    db.Column('news_id', db.Integer, db.ForeignKey('news.id',  ondelete='CASCADE'), primary_key=True),
    db.Column('tag_id',  db.Integer, db.ForeignKey('tags.id',  ondelete='CASCADE'), primary_key=True),
)


# ─── Modelos ──────────────────────────────────────────────────────────────────

class Category(db.Model):
    __tablename__ = 'categories'

    id         = db.Column(db.Integer, primary_key=True)
    name       = db.Column(db.String(100), nullable=False, unique=True)
    slug       = db.Column(db.String(100), nullable=False, unique=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    news = db.relationship('News', secondary=news_categories, back_populates='categories')

    def __repr__(self):
        return f'<Category {self.slug}>'


class Tag(db.Model):
    __tablename__ = 'tags'

    id         = db.Column(db.Integer, primary_key=True)
    name       = db.Column(db.String(50), nullable=False, unique=True)
    slug       = db.Column(db.String(50), nullable=False, unique=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    news = db.relationship('News', secondary=news_tags, back_populates='tags')

    def __repr__(self):
        return f'<Tag {self.slug}>'


class News(db.Model):
    __tablename__ = 'news'

    id             = db.Column(db.Integer, primary_key=True)
    title          = db.Column(db.String(255), nullable=False)
    slug           = db.Column(db.String(255), nullable=False, unique=True)
    summary        = db.Column(db.String(500))
    content_json   = db.Column(db.JSON, nullable=False)
    featured_image = db.Column(db.String(500))
    author_id      = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'))
    is_published   = db.Column(db.Boolean, default=False)
    published_at   = db.Column(db.DateTime)
    views_count    = db.Column(db.Integer, default=0)
    created_at     = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at     = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    author     = db.relationship('User', foreign_keys=[author_id])
    categories = db.relationship('Category', secondary=news_categories, back_populates='news')
    tags       = db.relationship('Tag',      secondary=news_tags,       back_populates='news')
    views      = db.relationship('NewsView',  back_populates='news', cascade='all, delete-orphan')
    comments   = db.relationship('Comment',   back_populates='news', cascade='all, delete-orphan')
    reactions  = db.relationship('Reaction',  back_populates='news', cascade='all, delete-orphan')

    __table_args__ = (
        db.Index('idx_news_published', 'is_published', 'published_at'),
        db.Index('idx_news_slug',      'slug'),
        db.Index('idx_news_author',    'author_id', 'created_at'),
    )

    def __repr__(self):
        return f'<News {self.slug}>'


class NewsView(db.Model):
    __tablename__ = 'news_views'

    id         = db.Column(db.Integer, primary_key=True)
    news_id    = db.Column(db.Integer, db.ForeignKey('news.id',  ondelete='CASCADE'), nullable=False)
    user_id    = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'))
    ip_address = db.Column(db.String(45))
    viewed_at  = db.Column(db.DateTime, default=datetime.utcnow)

    news = db.relationship('News', back_populates='views')
    user = db.relationship('User', foreign_keys=[user_id])

    __table_args__ = (
        db.Index('idx_news_views_count', 'news_id', 'viewed_at'),
        db.Index('idx_news_views_user',  'user_id', 'viewed_at'),
    )


class Comment(db.Model):
    __tablename__ = 'comments'

    id          = db.Column(db.Integer, primary_key=True)
    news_id     = db.Column(db.Integer, db.ForeignKey('news.id',     ondelete='CASCADE'), nullable=False)
    user_id     = db.Column(db.Integer, db.ForeignKey('users.id',    ondelete='SET NULL'))
    parent_id   = db.Column(db.Integer, db.ForeignKey('comments.id', ondelete='CASCADE'))
    content     = db.Column(db.Text, nullable=False)
    is_approved = db.Column(db.Boolean, default=True)
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at  = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    news    = db.relationship('News', back_populates='comments')
    user    = db.relationship('User', foreign_keys=[user_id])
    # Self-referential: um comentário pode ter respostas
    replies = db.relationship(
        'Comment',
        backref=db.backref('parent', remote_side='Comment.id'),
        foreign_keys='[Comment.parent_id]',
        cascade='all, delete-orphan',
    )

    __table_args__ = (
        db.Index('idx_comments_news',     'news_id', 'created_at'),
        db.Index('idx_comments_approved', 'news_id', 'is_approved', 'created_at'),
    )


class Reaction(db.Model):
    __tablename__ = 'reactions'

    id         = db.Column(db.Integer, primary_key=True)
    news_id    = db.Column(db.Integer, db.ForeignKey('news.id',  ondelete='CASCADE'), nullable=False)
    user_id    = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    type       = db.Column(db.Enum('like', 'love', 'clap', 'insightful', 'curious'), default='like')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    news = db.relationship('News', back_populates='reactions')
    user = db.relationship('User', foreign_keys=[user_id])

    __table_args__ = (
        db.UniqueConstraint('news_id', 'user_id', name='uq_reaction'),
    )
