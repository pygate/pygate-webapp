"""
Define the web application's relative routes and the business logic for each
"""

import os
from datetime import datetime
from flask import (
    render_template,
    flash,
    request,
    send_file,
    safe_join,
)
from werkzeug.utils import secure_filename
from sqlalchemy import desc
from google.protobuf.json_format import MessageToDict
from pygate_grpc.client import PowerGateClient
from pygate_grpc.ffs import get_file_bytes, bytes_to_chunks, chunks_to_bytes
from pygate import app, db
from pygate.models import Files, Ffs, Logs


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
            ffs = powergate.ffs.create()
            creation_date = datetime.now().replace(microsecond=0)
            filecoin_file_system = Ffs(
                ffs_id=ffs.id,
                token=ffs.token,
                creation_date=creation_date,
                default=True,
            )

            # Record new FFS creation in log table
            event = Logs(
                timestamp=creation_date,
                event="Created new Filecoin FileSystem (FFS): " + ffs.id,
            )
            db.session.add(event)
            db.session.commit()

            address = powergate.ffs.addrs_list(ffs.token)
            obj = MessageToDict(address)
            wallet = obj["addrs"][0]["addr"]

            # Record new Wallet creation in log table
            event = Logs(
                timestamp=creation_date, event="Created new Wallet: " + wallet,
            )
            db.session.add(event)

            db.session.add(filecoin_file_system)
            db.session.commit()
            ffs = Ffs.query.filter_by(default=True).first()

        try:
            # Create an iterator of the uploaded file using the helper function
            file_iterator = get_file_bytes(os.path.join(upload_path, file_name))
            # Convert the iterator into request and then add to the hot set (IPFS)
            file_hash = powergate.ffs.add_to_hot(
                bytes_to_chunks(file_iterator), ffs.token
            )
            # Push the file to Filecoin
            powergate.ffs.push(file_hash.cid, ffs.token)
            # Check that CID is pinned to FFS
            check = powergate.ffs.info(file_hash.cid, ffs.token)

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

            flash("'{}' uploaded to Filecoin.".format(file_name))

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
        addresses_dict = MessageToDict(addresses)

        for address in addresses_dict["addrs"]:
            # TODO: FIX ME https://github.com/pygate/pygate-gRPC/issues/27
            # balance = powergate.wallet.balance(address["addr"])
            wallets.append(
                {
                    "ffs": filecoin_filesystem.ffs_id,
                    "name": address["name"],
                    "address": address["addr"],
                    "type": address["type"],
                    "balance": "[fix me]",
                }
            )

    return render_template("wallets.html", wallets=wallets)


@app.route("/logs", methods=["GET"])
def logs():

    logs = Logs.query.all()
    return render_template("logs.html", logs=logs)


@app.route("/settings", methods=["GET"])
def settings():
    return render_template("settings.html")
