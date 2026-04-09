from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_wtf import CSRFProtect
from flask_mail import Mail
from flask_migrate import Migrate

db = SQLAlchemy()
login_manager = LoginManager()
csrf = CSRFProtect()
mail = Mail()
migrate = Migrate()


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

    return app
