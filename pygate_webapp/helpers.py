import os
from datetime import datetime
from flask import flash, current_app
from pygate_grpc.client import PowerGateClient
from pygate_grpc.ffs import get_file_bytes, bytes_to_chunks, chunks_to_bytes
from google.protobuf.json_format import MessageToDict
from pygate_webapp.database import db
from pygate_webapp.models import Ffs, Logs, Files


def create_ffs(default=False):
    """
    Create a new Powergate Filecoin Filesystem (FFS)
    """

    powergate = PowerGateClient(current_app.config["POWERGATE_ADDRESS"])

    if default == True:
        default_ffs = Ffs.query.filter_by(default=True).first()
        if default_ffs is not None:
            default_ffs.default = False
            db.session.commit()

    ffs = powergate.ffs.create()
    creation_date = datetime.now().replace(microsecond=0)
    filecoin_file_system = Ffs(
        ffs_id=ffs.id, token=ffs.token, creation_date=creation_date, default=default,
    )
    db.session.add(filecoin_file_system)

    # Record new FFS creation in log table
    event = Logs(
        timestamp=creation_date,
        event="Created new Filecoin FileSystem (FFS): " + ffs.id,
    )
    db.session.add(event)
    db.session.commit()

    # Record creation of new FFS wallet in log table
    address = powergate.ffs.addrs_list(ffs.token)
    obj = MessageToDict(address)
    wallet = obj["addrs"][0]["addr"]
    event = Logs(timestamp=creation_date, event="Created new Wallet: " + wallet,)
    db.session.add(event)
    db.session.commit()

    new_ffs = Ffs.query.filter_by(ffs_id=ffs.id).first()

    return new_ffs


def push_to_filecoin(upload_path, file_name):

    # Push file to Filecoin via Powergate
    powergate = PowerGateClient(current_app.config["POWERGATE_ADDRESS"])

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
        """TODO: DELETE CACHED COPIES OF FILE UPLOADS """

        # Note the upload date and file size
        upload_date = datetime.now().replace(microsecond=0)
        file_size = os.path.getsize(os.path.join(upload_path, file_name))

        # Save file information to database
        file_upload = Files(
            file_path=upload_path,
            file_name=file_name,
            upload_date=upload_date,
            file_size=file_size,
            CID=file_hash.cid,
            ffs_id=ffs.id,
        )

        # Record file upload in log table
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

    return ()
