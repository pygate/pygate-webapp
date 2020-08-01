from pygate_grpc.client import PowerGateClient
from google.protobuf.json_format import MessageToDict
from pygate import app, db
from datetime import datetime
from pygate.models import Ffs, Logs


def create_ffs(default=False):
    """
    Create a new Powergate Filecoin Filesystem (FFS)
    """

    powergate = PowerGateClient(app.config["POWERGATE_ADDRESS"])

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

    ffs = Ffs.query.filter_by(default=True).first()

    return ffs
