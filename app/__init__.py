""" This module initializes the Flask application and its components. """

from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_babel import Babel, get_locale
from flask_wtf.csrf import CSRFProtect

db = SQLAlchemy()
login_manager = LoginManager()
babel = Babel()
csrf = CSRFProtect()

# Define the supported languages for the application
languages = ["de", "en"]


def select_locale():
    """ Select the best matching locale from the request's accept languages. """
    # print("Available languages:", request.accept_languages)
    preferred_language = request.accept_languages.best_match(languages)
    # print(f"Selected language: {preferred_language}")
    return preferred_language


def create_app():
    """ Create and configure the Flask application. """
    app = Flask(__name__)
    app.config.from_object('config.Config')

    db.init_app(app)
    login_manager.init_app(app)
    babel.init_app(app, locale_selector=select_locale)
    csrf.init_app(app)

    app.config['BABEL_DEFAULT_LOCALE'] = 'en'
    app.config['BABEL_SUPPORTED_LOCALES'] = languages
    app.config["BABEL_TRANSLATION_DIRECTORIES"] = "translations"

    login_manager.login_view = 'auth.login'

    # ! Blueprints registration
    from app.views.main import main_bp
    app.register_blueprint(main_bp)
    from app.views.auth import auth_bp
    app.register_blueprint(auth_bp)
    from app.views.image import image_bp
    app.register_blueprint(image_bp)
    from app.views.user import user_bp
    app.register_blueprint(user_bp)
    from app.views.admin import admin_bp
    app.register_blueprint(admin_bp)
    from app.views.notification import notification_bp
    app.register_blueprint(notification_bp)

    return app


@login_manager.user_loader
def load_user(user_id):
    """ Load a user from the database by the user id. """
    from app.model.model import User
    return User.query.get(int(user_id))
