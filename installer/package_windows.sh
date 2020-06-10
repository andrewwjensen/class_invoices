#!/usr/bin/env bash
set -e

if [[ ! -e venv ]]; then
    $(which python) -m venv venv
fi

if [[ -f venv/bin/activate ]]; then
    source venv/bin/activate
else
    source venv/Scripts/activate
fi

rm -rf dist

mkdir -p build

python -m pip install --upgrade pip
pip install --upgrade -r requirements.txt
pip install --upgrade -r installer/win-requirements.txt
#pip install https://github.com/pyinstaller/pyinstaller/tarball/develop
pip install pyinstaller

python app_config.py installer/win_version_file.py build/win_version_file.py
pyinstaller ClassInvoices.spec

deactivate
