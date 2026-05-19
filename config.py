""" This module handles the Configuration settings for the Flask application.
    It loads environment variables and sets up the database URI, secret key, and other settings.
"""

import os
from dotenv import load_dotenv
load_dotenv()


class Config:
    """ Configuration class for the Flask application. """
    # Use environment variable if provided, otherwise fall back to a development key.
    # In production, set the SECRET_KEY env var to a strong unpredictable value.
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key')
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'SQLALCHEMY_DATABASE_URI', 'sqlite:///test.db')
    SQLALCHEMY_BINDS = {}
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    LANGUAGES = ['de', 'en']
    BABEL_DEFAULT_LOCALE = 'en'
