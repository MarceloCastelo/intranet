from flask import Flask, abort, request as flask_request
from flask_caching import Cache
from flask_compress import Compress
from flask_login import LoginManager, current_user
from flask_mail import Mail
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import CSRFProtect

db = SQLAlchemy()
login_manager = LoginManager()
csrf = CSRFProtect()
mail = Mail()
migrate = Migrate()
cache = Cache()
compress = Compress()


def create_app():
    app = Flask(__name__)

    from app.config import Config
    app.config.from_object(Config)

    # Extensões
    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)
    mail.init_app(app)
    migrate.init_app(app, db)
    cache.init_app(app)
    compress.init_app(app)

    # Login manager
    login_manager.login_view = "auth.login"
    login_manager.login_message = "Faça login para acessar esta página."
    login_manager.login_message_category = "warning"

    # Registrar models (necessário para Flask-Migrate descobrir todas as tabelas)
    from app import models  # noqa: F401

    # user_loader para Flask-Login
    from app.models.user import User

    @login_manager.user_loader
    def load_user(user_id: str):
        return db.session.get(User, int(user_id))

    # Blueprints
    from app.routes.auth import auth_bp
    from app.routes.main import main_bp
    from app.routes.users import users_bp
    from app.routes.news import news_bp
    from app.routes.banners import banners_bp
    from app.routes.events import events_bp
    from app.routes.faq import faq_bp
    from app.routes.polls import polls_bp
    from app.routes.gallery import gallery_bp
    from app.routes.extensions import extensions_bp
    from app.routes.services import services_bp
    from app.routes.interactions import interactions_bp
    from app.routes.audit import audit_bp
    from app.routes.ouvidoria import ouvidoria_bp
    from app.routes.modules import modules_bp
    from app.routes.approvals import approvals_bp
    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(users_bp)
    app.register_blueprint(news_bp)
    app.register_blueprint(banners_bp)
    app.register_blueprint(events_bp)
    app.register_blueprint(faq_bp)
    app.register_blueprint(polls_bp)
    app.register_blueprint(gallery_bp)
    app.register_blueprint(extensions_bp)
    app.register_blueprint(services_bp)
    app.register_blueprint(interactions_bp)
    app.register_blueprint(audit_bp)
    app.register_blueprint(ouvidoria_bp)
    app.register_blueprint(modules_bp)
    app.register_blueprint(approvals_bp)

    # ── Injetar estado dos módulos em todos os templates ────────────────────
    @app.context_processor
    def inject_active_modules():
        try:
            from app.models.content import SiteModule
            mods = SiteModule.query.all()
            return {'active_modules': {m.key: m.is_active for m in mods}}
        except Exception:
            return {'active_modules': {}}

    # ── Contador de aprovações pendentes para o sidebar ─────────────────────
    @app.context_processor
    def inject_pending_approvals():
        def pending_approvals_count():
            try:
                from app.models.approval import ContentApproval
                return ContentApproval.query.filter_by(status='pending').count()
            except Exception:
                return 0
        return {'pending_approvals_count': pending_approvals_count}

    # ── Proteção de rotas por módulo (non-admin → 404 se módulo desativado) ─
    # Blueprints mapeados 1:1 para chaves de módulo
    _MODULE_BLUEPRINTS = {
        'news', 'events', 'faq', 'polls',
        'gallery', 'extensions', 'services',
        'pages', 'links',
    }

    @app.before_request
    def _enforce_module_access():
        endpoint = flask_request.endpoint or ''
        if '.' not in endpoint:
            return
        bp = endpoint.split('.')[0]
        if bp not in _MODULE_BLUEPRINTS:
            return
        # Admin bypassa qualquer restrição de módulo
        if current_user.is_authenticated and current_user.is_admin:
            return
        try:
            from app.models.content import SiteModule
            mod = SiteModule.query.filter_by(key=bp).first()
            if mod is not None and not mod.is_active:
                abort(404)
        except Exception:
            pass

    return app
