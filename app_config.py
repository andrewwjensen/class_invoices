# from PyQt5.QtCore import QSettings
import os

import wx

PUBLISHER_NAME = 'AndyJensen'
APP_NAME = 'ClassInvoices'

DEFAULT_DOC_DIR_KEY = 'default_dir'
DEFAULT_CSV_DIR_KEY = 'csv_dir'
GMAIL_TOKEN_KEY = 'gmail_token'

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
