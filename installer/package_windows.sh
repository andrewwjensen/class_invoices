#!/usr/bin/env bash

# Make sure we exit if any errors occur rather than blindly continuing
set -e

# Set up the virtual Python environment to avoid messing with system or user modules
if [[ ! -e venv ]]; then
    $(which python) -m venv venv
fi
# Windows may install activate script into one of two locations:
if [[ -f venv/bin/activate ]]; then
    source venv/bin/activate
else
    source venv/Scripts/activate
fi

# Install prerequisite packages
python -m pip install --upgrade pip
pip install --upgrade -r requirements.txt
pip install --upgrade -r installer/requirements-win.txt
pip install pyinstaller

# Clean up any previous build
rm -rf build dist
mkdir -p build

# Perform substitutions and copy win_version_file.py into build dir
python app_config.py installer/win_version_file.py build/win_version_file.py

# Finally, package everything into the app
pyinstaller ClassInvoices.spec

deactivate
