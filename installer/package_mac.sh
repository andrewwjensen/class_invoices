#!/usr/bin/env bash

# Make sure we exit if any errors occur rather than blindly continuing
set -e

# Set up the virtual Python environment to avoid messing with system or user modules
if [[ ! -e venv ]]; then
    python3 -m venv venv
fi
source venv/bin/activate

# Install prerequisite packages
python -m pip install --upgrade pip
pip install --upgrade -r requirements.txt
pip install --upgrade -r installer/requirements-mac.txt
pip install --upgrade pyinstaller

# Clean up any previous build
rm -rf build dist

# Package everything into the application bundle
pyinstaller ClassInvoices.spec

deactivate
