"""
Define the web application's relative routes and the business logic for each
"""

import os
import json
from datetime import datetime
from flask import (
    render_template,
    redirect,
    url_for,
    flash,
    request,
    send_file,
    safe_join,
)
from werkzeug.utils import secure_filename
from google.protobuf.json_format import MessageToDict
from pygate_grpc.client import PowerGateClient
from pygate_grpc.ffs import get_file_bytes, bytes_to_chunks, chunks_to_bytes
from pygate import app, db
from pygate.models import Files, Ffs, Logs
from pygate.forms import NewFfsForm, FfsConfigForm
from pygate.helpers import create_ffs


@app.route("/", methods=["GET"])
@app.route("/files", methods=["GET", "POST"])
def files():
    """
    Upload a new file to add to Filecoin via Powergate FFS and
    list files previously added. Allow users to download files from
    Filecoin via this list.
    """

    # Uploading a new file
    if request.method == "POST":

        # Use the default upload directory configured for the app
        upload_path = app.config["UPLOADDIR"]
        if not os.path.exists(upload_path):
            os.makedirs(upload_path)
        # Get the file and filename from the request
        upload = request.files["uploadfile"]
        file_name = secure_filename(upload.filename)

        try:
            # Save the uploaded file
            upload.save(os.path.join(upload_path, file_name))
        except:
            # Respond if the user did not provide a file to upload
            stored_files = Files.query.all()
            flash("Please choose a file to upload to Filecoin")
            return render_template("files.html", stored_files=stored_files)

        """TODO: ENCRYPT FILE"""

        # Push file to Filecoin via Powergate
        powergate = PowerGateClient(app.config["POWERGATE_ADDRESS"])
        # Retrieve information for default Filecoin FileSystem (FFS)
        ffs = Ffs.query.filter_by(default=True).first()
        if ffs is None:
            # No FFS exists yet so create one
            ffs = create_ffs(default=True)
        try:
            # Create an iterator of the uploaded file using the helper function
            file_iterator = get_file_bytes(os.path.join(upload_path, file_name))
            # Convert the iterator into request and then add to the hot set (IPFS)
            file_hash = powergate.ffs.stage(bytes_to_chunks(file_iterator), ffs.token)
            # Push the file to Filecoin
            powergate.ffs.push(file_hash.cid, ffs.token)

            # Note the upload date and file size
            upload_date = datetime.now().replace(microsecond=0)
            file_size = os.path.getsize(os.path.join(upload_path, file_name))

            """TODO: DELETE CACHED COPIES OF FILE UPLOADS """

            # Save file information to database
            file_upload = Files(
                file_path=upload_path,
                file_name=file_name,
                upload_date=upload_date,
                file_size=file_size,
                CID=file_hash.cid,
                ffs_id=ffs.id,
            )

            # Record upload in log table
            event = Logs(
                timestamp=upload_date,
                event="Uploaded "
                + file_name
                + " (CID: "
                + file_hash.cid
                + ") to Filecoin.",
            )
            db.session.add(file_upload)
            db.session.add(event)
            db.session.commit()

        except Exception as e:
            # Output error message if pushing to Filecoin fails
            flash("'{}' failed to upload to Filecoin. {}".format(file_name, e))

            # Update log table with error
            event = Logs(
                timestamp=datetime.now().replace(microsecond=0),
                event="Upload ERROR: " + file_name + " " + str(e),
            )
            db.session.add(event)
            db.session.commit()

            """TODO: RESPOND TO SPECIFIC STATUS CODE DETAILS
            (how to isolate these? e.g. 'status_code.details = ...')"""

    stored_files = Files.query.all()

    return render_template("files.html", stored_files=stored_files)


@app.route("/download/<cid>", methods=["GET"])
def download(cid):
    """
    Retrieve a file from Filecoin via IPFS using Powergate and offer the user
    the option to save it to their machine.
    """

    # Retrieve File and FFS info using the CID
    file = Files.query.filter_by(CID=cid).first()
    ffs = Ffs.query.get(file.ffs_id)

    try:
        # Retrieve data from Filecoin
        powergate = PowerGateClient(app.config["POWERGATE_ADDRESS"])
        data_ = powergate.ffs.get(file.CID, ffs.token)

        # Save the downloaded data as a file
        # Use the default download directory configured for the app
        download_path = app.config["DOWNLOADDIR"]
        if not os.path.exists(download_path):
            os.makedirs(download_path)

        with open(os.path.join(download_path, file.file_name), "wb") as out_file:
            # Iterate over the data byte chunks and save them to an output file
            for data in data_:
                out_file.write(data)

        # Create path to download file
        safe_path = safe_join("../" + app.config["DOWNLOADDIR"], file.file_name)

        # Update log table with download information
        event = Logs(
            timestamp=datetime.now().replace(microsecond=0),
            event="Downloaded "
            + file.file_name
            + " (CID: "
            + file.CID
            + ") from Filecoin.",
        )
        db.session.add(event)
        db.session.commit()

        # Offer the file for download to local machine
        return send_file(safe_path, as_attachment=True)
        """TODO: CLEAR CACHED FILES IN DOWNLOAD DIRECTORY"""

    except Exception as e:
        # Output error message if download from Filecoin fails
        flash("failed to download '{}' from Filecoin. {}".format(file.file_name, e))

        # Update log table with error
        event = Logs(
            timestamp=datetime.now().replace(microsecond=0),
            event="Download ERROR: "
            + file.file_name
            + " CID: "
            + file.CID
            + " "
            + str(e),
        )
        db.session.add(event)
        db.session.commit()

        stored_files = Files.query.all()

        return render_template("files.html", stored_files=stored_files)


@app.route("/wallets", methods=["GET"])
def wallets():
    """
    Retrieve all wallets from all FFSes and save them in a list for
    presentation on the UI template
    """

    powergate = PowerGateClient(app.config["POWERGATE_ADDRESS"])

    ffses = Ffs.query.all()
    wallets = []

    for filecoin_filesystem in ffses:
        addresses = powergate.ffs.addrs_list(filecoin_filesystem.token)

        for address in addresses.addrs:
            balance = powergate.wallet.balance(address.addr)
            wallets.append(
                {
                    "ffs": filecoin_filesystem.ffs_id,
                    "name": address.name,
                    "address": address.addr,
                    "type": address.type,
                    "balance": str(balance.balance),
                }
            )

    return render_template("wallets.html", wallets=wallets)


@app.route("/logs", methods=["GET"])
def logs():
    """
    Display all the log entries recorded by the application
    """

    logs = Logs.query.all()

    return render_template("logs.html", logs=logs)


@app.route("/config", methods=["GET"])
@app.route("/config/<ffs_id>", methods=["GET"])
def config(ffs_id=None):
    """
    Create and edit FFS config settings
    """
    NewFFSForm = NewFfsForm()

    powergate = PowerGateClient(app.config["POWERGATE_ADDRESS"])

    if ffs_id == None:
        active_ffs = Ffs.query.filter_by(default=True).first()
    else:
        active_ffs = Ffs.query.filter_by(ffs_id=ffs_id).first()

    if active_ffs == None:
        active_ffs = create_ffs(default=True)

    default_config = powergate.ffs.default_config(active_ffs.token)

    """TODO: Move MessageToDict helper to pygate-grpc client and return dict"""
    msg_dict = MessageToDict(default_config)

    print(msg_dict)

    # populate form values from config dictionary
    try:
        hot_enabled = msg_dict["defaultStorageConfig"]["hot"]["enabled"]
    except KeyError:
        hot_enabled = False
    try:
        allow_unfreeze = msg_dict["defaultStorageConfig"]["hot"]["allowUnfreeze"]
    except KeyError:
        allow_unfreeze = False
    try:
        add_timeout = msg_dict["defaultStorageConfig"]["hot"]["ipfs"]["addTimeout"]
    except KeyError:
        add_timeout = 0
    try:
        cold_enabled = msg_dict["defaultStorageConfig"]["cold"]["enabled"]
    except KeyError:
        cold_enabled = False
    try:
        rep_factor = msg_dict["defaultStorageConfig"]["cold"]["filecoin"]["repFactor"]
    except KeyError:
        rep_factor = 0
    try:
        deal_min_duration = msg_dict["defaultStorageConfig"]["cold"]["filecoin"][
            "dealMinDuration"
        ]
    except KeyError:
        deal_min_duration = 0
    try:
        excluded_miners_array = msg_dict["defaultStorageConfig"]["cold"]["filecoin"][
            "excludedMiners"
        ]
        # Break out array into comma separate values
        excluded_miners = ""
        for miner in excluded_miners_array:
            excluded_miners += miner
            # Don't add a comma if this is only or last item in array
            if (len(excluded_miners_array)) > 1:
                if (excluded_miners_array.index(miner) + 1) != len(
                    excluded_miners_array
                ):
                    excluded_miners += ","
    except KeyError:
        excluded_miners = None
    try:
        trusted_miners_array = msg_dict["defaultStorageConfig"]["cold"]["filecoin"][
            "trustedMiners"
        ]
        # Break out array into comma separate values
        trusted_miners = ""
        for miner in trusted_miners_array:
            trusted_miners += miner
            # Don't add a comma if this is only or last item in array
            if (len(trusted_miners_array)) > 1:
                if (trusted_miners_array.index(miner) + 1) != len(trusted_miners_array):
                    trusted_miners += ","
    except KeyError:
        trusted_miners = None
    try:
        country_codes_array = msg_dict["defaultStorageConfig"]["cold"]["filecoin"][
            "countryCodes"
        ]
        # Break out array into comma separate values
        country_codes = ""
        for country in country_codes_array:
            country_codes += country
            # Don't add a comma if this is only or last item in array
            if (len(country_codes_array)) > 1:
                if (country_codes_array.index(country) + 1) != len(country_codes_array):
                    country_codes += ","
    except KeyError:
        country_codes = None
    try:
        renew_enabled = msg_dict["defaultStorageConfig"]["cold"]["filecoin"]["renew"][
            "enabled"
        ]
    except KeyError:
        renew_enabled = False
    try:
        renew_threshold = msg_dict["defaultStorageConfig"]["cold"]["filecoin"]["renew"][
            "threshold"
        ]
    except KeyError:
        renew_threshold = 0

    wallet_address = msg_dict["defaultStorageConfig"]["cold"]["filecoin"]["addr"]

    try:
        max_price = msg_dict["defaultStorageConfig"]["cold"]["filecoin"]["maxPrice"]
    except KeyError:
        max_price = 0
    try:
        repairable = msg_dict["defaultStorageConfig"]["repairable"]
    except KeyError:
        repairable = True

    # Instantiate config form
    ConfigForm = FfsConfigForm()
    ConfigForm.make_default.data = active_ffs.default
    ConfigForm.hot_enabled.data = hot_enabled
    ConfigForm.allow_unfreeze.data = allow_unfreeze
    ConfigForm.add_timeout.data = add_timeout
    ConfigForm.cold_enabled.data = cold_enabled
    ConfigForm.rep_factor.data = rep_factor
    ConfigForm.deal_min_duration.data = deal_min_duration
    ConfigForm.excluded_miners.data = excluded_miners
    ConfigForm.trusted_miners.data = trusted_miners
    ConfigForm.country_codes.data = country_codes
    ConfigForm.renew_enabled.data = renew_enabled
    ConfigForm.renew_threshold.data = renew_threshold
    ConfigForm.max_price.data = max_price
    ConfigForm.repairable.data = repairable

    all_ffses = Ffs.query.order_by((Ffs.default).desc()).all()

    return render_template(
        "config.html",
        NewFfsForm=NewFFSForm,
        FfsConfigForm=ConfigForm,
        wallet_address=wallet_address,
        active_ffs=active_ffs,
        all_ffses=all_ffses,
    )


@app.route("/new_ffs", methods=["POST"])
def new_ffs():
    """
    Create a new Filecoin Filesystem (FFS), including a default wallet and config
    """
    form = NewFfsForm()

    new_ffs = create_ffs(default=form.default.data)

    return redirect(url_for("config", ffs_id=new_ffs.ffs_id))


@app.route("/change_config/<ffs_id>/<wallet>", methods=["POST"])
def change_config(ffs_id, wallet):
    """
    Change the default configuration for a FFS, triggering a change to all files
    that were uploaded using that config.
    """

    ffs = Ffs.query.filter_by(ffs_id=ffs_id).first()

    form = FfsConfigForm(request.form)

    # Change default FFS
    if form.make_default.data == True:
        current_default_ffs = Ffs.query.filter_by(default=True).first()
        if current_default_ffs is not None:
            current_default_ffs.default = False
        ffs.default = True
        db.session.commit()

    exlcude_miners = []
    trust_miners = []
    countries = []
    exclude_miners = form.excluded_miners.data.split(",")
    trust_miners = form.trusted_miners.data.split(",")
    countries = form.country_codes.data.split(",")

    new_config = {
        "hot": {
            "enabled": form.hot_enabled.data,
            "allowUnfreeze": form.allow_unfreeze.data,
            "ipfs": {"addTimeout": form.add_timeout.data},
        },
        "cold": {
            "enabled": form.cold_enabled.data,
            "filecoin": {
                "repFactor": form.rep_factor.data,
                "dealMinDuration": form.deal_min_duration.data,
                "excludedMiners": exclude_miners,
                "trustedMiners": trust_miners,
                "countryCodes": countries,
                "renew": {
                    "enabled": form.renew_enabled.data,
                    "threshold": form.renew_threshold.data,
                },
                "addr": wallet,
                "maxPrice": form.max_price.data,
            },
        },
        "repairable": True,
    }

    new_config_json = json.dumps(new_config)

    powergate = PowerGateClient(app.config["POWERGATE_ADDRESS"])
    powergate.ffs.set_default_config(new_config_json, ffs.token)

    # Log the configuration change
    event = Logs(
        timestamp=datetime.now().replace(microsecond=0),
        event="Changed default configuration for FFS " + ffs.ffs_id,
    )
    db.session.add(event)
    db.session.commit()

    return redirect(url_for("config", ffs_id=ffs_id))
