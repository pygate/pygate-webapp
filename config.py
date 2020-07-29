"""
Global settings for Pygate application
"""

import os

BASEDIR = os.path.abspath(os.path.dirname(__file__))
UPLOADDIR = "uploads/"
DOWNLOADDIR = "downloads/"
POWERGATE_ADDRESS = "127.0.0.1:5002"

# change to os.environ settings in production
SQLALCHEMY_DATABASE_URI = "sqlite:///" + os.path.join(BASEDIR, "pygate.db")
SQLALCHEMY_ECHO = False

# change to a long random code (e.g. UUID) when pushing to production
SECRET_KEY = os.environ.get("SECRET_KEY") or "you-will-never-guess"
