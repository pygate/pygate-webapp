from setuptools import setup, find_packages

package_name = "pygate_webapp"

# read the contents of your README file
from os import path

this_directory = path.abspath(path.dirname(__file__))
with open(path.join(this_directory, "README.md"), encoding="utf-8") as f:
    long_description = f.read()

with open(path.join(this_directory, package_name, "VERSION"), encoding="utf-8") as f:
    version = f.read()

setup(
    install_requires=[
        "click==7.1.2",
        "deprecated==1.2.10",
        "flask==1.1.2",
        "flask-sqlalchemy==2.4.4",
        "flask-wtf==0.14.3",
        "grpcio==1.30.0",
        "itsdangerous==1.1.0",
        "jinja2==2.11.2",
        "markupsafe==1.1.1",
        "protobuf==3.12.4",
        "pygate-grpc==0.0.11",
        "six==1.15.0",
        "sqlalchemy==1.3.18",
        "werkzeug==1.0.1",
        "wrapt==1.12.1",
        "wtforms==2.3.3",
    ],
    name=package_name,
    version=version,
    description="A Flask Web Application for PyGate gRPC client (Powergate)",
    url="https://github.com/pygate/pygate-webbapp",
    entry_points = {
        'console_scripts': ['pygate-webapp=pygate_webapp.cli:run'],
    },
    author="Pygate Team",
    author_email="info@pygate.com",
    license="MIT",
    package_data={'': ['VERSION']},
    packages=[package_name],
    long_description=long_description,
    long_description_content_type="text/markdown",
    zip_safe=False,
    classifiers=[
        "Development Status :: 3 - Alpha",  # Chose either "3 - Alpha", "4 - Beta" or "5 - Production/Stable" as the current state of your package
        "Intended Audience :: Developers",  # Define that your audience are developers
        "Intended Audience :: Information Technology",
        "Topic :: Software Development :: Build Tools",
        "License :: OSI Approved :: MIT License",  # Again, pick a license
        "Programming Language :: Python :: 3",  # Specify which pyhton versions that you want to support
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
    ],
)
