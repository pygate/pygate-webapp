"""
Intialize the Pygate application
"""
import os

from flask import Flask
from flask_sqlalchemy import SQLAlchemy


def create_app():
    from pygate_webapp.config import app_config
    from pygate_webapp.database import db

    env = os.getenv("FLASK_ENV", "dev")

    config = app_config[env]
    app = Flask(__name__)
    app.config.from_object(config)

    db.init_app(app)

    with app.app_context():
        from . import routes, models  # Import routes
        db.create_all()  # Create sql tables for our data models

        return app

