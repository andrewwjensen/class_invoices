# Class Invoices
 
This is an application to read a CSV file of class registrations and generate
family invoices.

It is compatible with Python 3+ only (not compatible with Python 2.x). It
uses WxPython, with installer created by PyInstaller.

### Ubuntu Prerequisites

Run `bash install-prerequisites.sh` to install these Ubuntu system packages:
  * freeglut3
  * freeglut3-dev
  * libgstreamer-plugins-base1.0-dev
  * libgtk-3-dev
  * libgtk2.0-dev
  * libjpeg-dev
  * libnotify-dev
  * libsdl1.2-dev
  * libsm-dev
  * libtiff-dev
  * libwebkitgtk-3.0-dev
  * libwebkitgtk-dev

### Environment Setup

I recommend using a Python virtual environment to install the below dependencies
 into, to avoid polluting your system. To do so:
* `pip3 install virtualenv`
* `virtualenv -p /usr/bin/python3 venv`
* `source ./venv/bin/activate`
* Install the Python packages as directed below
* Run the application: `./ClassInvoices.py`
* Deactivate the virtual environment: `deactivate`

### Python Dependencies

Additional Python modules required (install with `pip install -r requirements.txt`):
  * google-api-python-client
  * google-auth-oauthlib
  * oauthlib
  * pymupdf (optional, but recommended; faster and more full featured than the default PyPDF2)
  * wxPython
  * z3c.rml

On Ubuntu, to install the binary of wxpython instead of building from sources:
  ```bash
  pip install -f https://extras.wxpython.org/wxPython4/extras/linux/gtk3/ubuntu-18.04 wxpython
  ```
