"""
Provide launch script for the Pygate application
"""

from pygate import app

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")
