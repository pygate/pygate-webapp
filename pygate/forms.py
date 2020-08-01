from flask_wtf import FlaskForm
from wtforms import BooleanField


class FfsForm(FlaskForm):
    default = BooleanField("Make default?")
