# Application to read a CSV file of class registrations and generate family invoices.

Written for Python3, uses WxPython and Qt, with installer created with PyInstaller.

Additional installation required on Ubuntu:
* `sudo apt install` these packages:
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
