# pygate-webapp
A Filecoin Flask template application for Python developers

# Installation
* Clone files and cd to directory:  
  `git clone https://github.com/pygate/pygate-webapp && cd pygate-webapp`  
* Set up virtualenv:  
  `virtualenv venv`  
* Activate virtualenv:  
  `source venv/bin/activate`  
* Install requirements:  
  `pip install -r requirements.txt`
* Create the application database:  
  `python create_db.py`
 * pygate-webapp is built using the [Python Flask](https://www.fullstackpython.com/flask.html) framework. To start the built-in development server:  
 `python run.py`
* Go to `localhost:5000` in your browser to use the app.
* This is a development release of the pygate-webapp. It is designed to work with a Dockerized [Localnet Powergate](https://docs.textile.io/powergate/localnet/). It assumed this is running at the `127.0.0.1:5002` address. You can change the POWERGATE_ADDRESS in the `config.py` file.
* Upload a file from your local machine to add it to the Filecoin Localnet.
