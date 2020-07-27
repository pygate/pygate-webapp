"""
Define the web application's relative routes and the business logic for each
"""

import os
from datetime import datetime
from flask import render_template, flash, request
from werkzeug.utils import secure_filename
from pygate_grpc.client import PowerGateClient
from pygate import app, db
from pygate.models import Uploads, Ffs


@app.route("/", methods=["GET"])
@app.route("/upload", methods=["GET", "POST"])
def upload():
    """Upload a new file to add to Filecoin via Powergate FFS"""

    # Uploading a new file
    if request.method == "POST":
        # Use the default upload directory configured for the app
        upload_path = app.config["UPLOADDIR"]
        if not os.path.exists(upload_path):
            os.makedirs(upload_path)
        # Get the file and filename from the request
        upload = request.files["uploadfile"]
        file_name = secure_filename(upload.filename)

        """TODO: ENCRYPT FILE"""

        # Save the uploaded file
        upload.save(os.path.join(upload_path, file_name))

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
            db.session.add(filecoin_file_system)
            db.session.commit()

        # Create an iterator of the uploaded file using the helper function
        file_iterator = powergate.ffs.get_file_bytes(
            os.path.join(upload_path, file_name)
        )
        # Convert the iterator into request and then add to the hot set (IPFS)
        file_hash = powergate.ffs.add_to_hot(
            powergate.ffs.bytes_to_chunks(file_iterator), ffs.token
        )
        # Push the file to Filecoin
        powergate.ffs.push(file_hash.cid, ffs.token)
        # Check that CID is pinned to FFS
        check = powergate.ffs.info(file_hash.cid, ffs.token)

        # Note the upload date and file size
        upload_date = datetime.now().replace(microsecond=0)
        file_size = os.path.getsize(os.path.join(upload_path, file_name))

        """TODO: DELETE CACHED COPY OF FILE? """

        # Save file information to database
        file_upload = Uploads(
            file_path=upload_path,
            file_name=file_name,
            upload_date=upload_date,
            file_size=file_size,
            CID=file_hash.cid,
        )
        db.session.add(file_upload)
        db.session.commit()

        flash("'{}' uploaded to Filecoin. CID: {}".format(file_name, file_hash.cid))

    return render_template("upload.html")


@app.route("/storage", methods=["GET"])
def storage():
    return render_template("storage.html")


@app.route("/wallets", methods=["GET"])
def wallets():
    return render_template("wallets.html")


@app.route("/logs", methods=["GET"])
def logs():
    return render_template("logs.html")


@app.route("/settings", methods=["GET"])
def settings():
    return render_template("settings.html")
