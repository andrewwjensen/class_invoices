#!/usr/bin/env bash

pip3 install virtualenv

if [[ ! -e venv ]]; then
    virtualenv -p $(which python) venv
fi

source venv/Scripts/activate

rm -rf dist

mkdir -p build

pip install --uprade pip
pip install -r requirements.txt
pip install -r installer/win-requirements.txt
pip install https://github.com/pyinstaller/pyinstaller/tarball/develop

python app_config.py installer/win_version_file.py build/win_version_file.py
pyinstaller ClassInvoices.spec

deactivate
