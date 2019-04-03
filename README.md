# Application to read a CSV file of class registrations and generate family invoices.

Written for Python 3 only (not compatible with Python 2), uses WxPython and Qt, with installer created with PyInstaller.

Additional installation required on Ubuntu:
* Run `bash install-prerequisites.sh` to install these system packages:
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

* Additional Python modules required (install with `pip install -r requirements.txt`):
  * google-api-python-client
  * google-auth-oauthlib
  * oauthlib
  * wxpython
  * z3c.rml
