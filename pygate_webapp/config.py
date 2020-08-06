"""
Global settings for Pygate application
"""

import os
import logging


class Config:
    """Parent configuration class."""

    ENV = os.getenv("FLASK_ENV", "dev")
    DEBUG = os.getenv("FLASK_DEBUG", True)
    APP_LOG_LEVEL = logging.INFO

    BASEDIR = os.path.abspath(os.path.dirname(__file__))
    UPLOADDIR = "_uploads/"
    DOWNLOADDIR = "_downloads/"
    POWERGATE_ADDRESS = "127.0.0.1:5002"

    # change to os.environ settings in production
    SQLALCHEMY_DATABASE_URI = "sqlite:///" + os.path.join(BASEDIR, "pygate.db")
    SQLALCHEMY_ECHO = False
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    SECRET_KEY = os.environ.get("SECRET_KEY") or "you-will-never-guess"


class TestingConfig(Config):
    """Configurations for Testing"""

    pass


class DevelopmentConfig(Config):
    """Configurations for Development."""

    APP_LOG_LEVEL = logging.DEBUG


class StagingConfig(Config):
    """Configurations for Staging."""

    pass


class ProductionConfig(Config):
    """Configurations for Production."""

    DEBUG = False


app_config = {
    "test": TestingConfig,
    "dev": DevelopmentConfig,
    "staging": StagingConfig,
    "prod": ProductionConfig,
}

