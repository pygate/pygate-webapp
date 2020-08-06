import argparse
import logging

from .version import __version__
from pygate_webapp import create_app

def parse_cli_commands(app):
    parser = argparse.ArgumentParser(description='PyGate gRPC - Web Application')

    parser.add_argument('--version', action='version', version=f'PyGate Web Application - v{__version__}')
    parser.add_argument('--verbose', '-v', action='store_true', help='verbose flag' )
    parser.add_argument('--powergate-addr', '-p', type=str, help='Powergate address')
    parser.add_argument('--upload', '-u', type=str, help='Upload directory')
    parser.add_argument('--download', '-d', type=str, help='Download directory')

    args = parser.parse_args()

    if args.verbose:
        app.config["APP_LOG_LEVEL"] = logging.DEBUG

    if args.powergate_addr:
        app.config["POWERGATE_ADDRESS"] = args.powergate_addr
    
    if args.upload:
        app.config["UPLOADDIR"] = args.upload

    if args.download:
        app.config["DOWNLOADDIR"] = args.download
    
    return args

def run():
    app = create_app()
    args = parse_cli_commands(app)
    app.run(debug=app.config["DEBUG"], host="0.0.0.0")