#!/usr/bin/env bash

pip3 install virtualenv

if [[ ! -e venv ]]; then
    virtualenv -p $(which python3) venv
fi

source venv/bin/activate

pip install -r requirements.txt
pip install -r installer/install-requirements.txt

rm -rf dist

pyinstaller ClassInvoices.spec

deactivate
