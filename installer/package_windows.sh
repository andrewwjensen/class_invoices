#!/usr/bin/env bash

pip3 install virtualenv

if [[ ! -e venv ]]; then
    virtualenv -p $(which python) venv
fi

if [[ -x venv/bin/activate ]]; then
    source venv/bin/activate
else
    source venv/Scripts/activate
fi

rm -rf dist

mkdir -p build

pip install --upgrade pip
pip install --upgrade -r requirements.txt
pip install --upgrade -r installer/win-requirements.txt
pip install https://github.com/pyinstaller/pyinstaller/tarball/develop

python app_config.py installer/win_version_file.py build/win_version_file.py
pyinstaller ClassInvoices.spec

deactivate
