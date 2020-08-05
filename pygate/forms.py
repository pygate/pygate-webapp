from flask_wtf import FlaskForm
from wtforms import BooleanField, IntegerField, StringField


class UploadForm(FlaskForm):
    make_package = BooleanField("Create one compressed package from multiple files?")
    package_name = StringField("Package name")


class NewFfsForm(FlaskForm):
    default = BooleanField("Make default?")


class FfsConfigForm(FlaskForm):
    make_default = BooleanField("Default FFS")
    hot_enabled = BooleanField("Hot storage (IPFS) enabled")
    allow_unfreeze = BooleanField("Allow unfreeze")
    add_timeout = IntegerField("Add timeout (seconds)")
    cold_enabled = BooleanField("Cold storage (Filecoin) enabled")
    rep_factor = IntegerField("Number of replications")
    deal_min_duration = IntegerField("Duration of storage deal (epochs)")
    excluded_miners = StringField("Excluded miners")
    trusted_miners = StringField("Trusted miners")
    country_codes = StringField("Country codes")
    renew_enabled = BooleanField("Renew deal")
    renew_threshold = IntegerField("Deal renewal threshold (epochs)")
    max_price = IntegerField("Maximum deal price (FIL)")
    repairable = BooleanField("Repairable")
