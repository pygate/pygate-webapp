"""
Create the application database if it doesn't already exist
"""

from pygate import db

db.create_all()
