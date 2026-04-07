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

    # Blueprints (serão registrados conforme implementados)
    # from app.routes.auth import auth_bp
    # app.register_blueprint(auth_bp)

    return app
