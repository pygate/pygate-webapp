from flask_wtf import FlaskForm
from wtforms import BooleanField, IntegerField


class NewFfsForm(FlaskForm):
    default = BooleanField("Make default?")


class FfsConfigForm(FlaskForm):
    hot_enabled = BooleanField("Hot Storage (IPFS) Enabled")
    allow_unfreeze = BooleanField("Allow Unfreeze")
    add_timeout = IntegerField("Add Timeout")
    cold_enabled = BooleanField("Cold Storage (Filecoin) Enabled")
