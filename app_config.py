# coding=utf-8
import os
import tempfile

import wx

PUBLISHER_NAME = 'AndyJensen'
APP_AUTHOR = 'Andrew W. Jensen'
APP_NAME = 'ClassInvoices'
APP_DESCRIPTION = 'Create invoices for classes from registration info.'
APP_VERSION = '1.1.0'
# Must be a 4-tuple for Windows packaging:
APP_VERSION_TUPLE = '(1, 1, 0, 0)'
APP_ID = 'com.thejensenfam.classinvoices'
APP_COPYRIGHT = f'© 2020, {APP_AUTHOR}, All Rights Reserved'

DEFAULT_DOC_DIR_KEY = 'default_dir'
DEFAULT_CSV_DIR_KEY = 'csv_dir'
GMAIL_TOKEN_KEY = 'gmail_token'

LOG_PATH = os.path.join(tempfile.gettempdir(), 'ClassInvoices.log')

DEFAULTS = {
    DEFAULT_DOC_DIR_KEY: os.path.expanduser('~/Documents/'),
    DEFAULT_CSV_DIR_KEY: os.path.expanduser('~/Documents/'),
}

conf = None


def create_config():
    global conf
    if conf is None:
        conf = wx.FileConfig(APP_NAME, PUBLISHER_NAME)
        for k, v in DEFAULTS.items():
            if not conf.Exists(k):
                if isinstance(v, int):
                    conf.WriteInt(k, v)
                else:
                    conf.Write(k, v)
        conf.Flush()


def substitute_app_values(string):
    """Replace all "{APP_*}" substitutions found in string with the value of the global variable."""
    app_parameters = [item for item in globals() if item.startswith('APP_')]
    kwargs = {k: eval(k) for k in app_parameters}
    return string.format(**kwargs)


def main():
    """Read filename in arg 1, substitute values, and write output as filename in arg 2."""
    import sys
    with open(sys.argv[1], 'rb') as f:
        output = substitute_app_values(f.read().decode())
    with open(sys.argv[2], 'wb') as f:
        f.write(output.encode())


if __name__ == '__main__':
    main()
