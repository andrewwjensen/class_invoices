#!/usr/bin/env bash

pip3 install virtualenv

if [[ ! -e venv ]]; then
    virtualenv -p /usr/local/bin/python3 venv
fi

source venv/bin/activate

pip install -r requirements.txt
pip install https://github.com/pyinstaller/pyinstaller/tarball/develop

rm -rf dist

pyinstaller ClassInvoices.spec

deactivate
