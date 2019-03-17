# from PyQt5.QtCore import QSettings
import os

import wx

PUBLISHER_NAME = 'AndyJensen'
APP_NAME = 'ClassInvoices'

DEFAULT_DOC_DIR_KEY = 'default_dir'
DEFAULT_CSV_DIR_KEY = 'csv_dir'
RECENT_FILES_KEY = 'recent'
POS_H_KEY = 'x'
POS_V_KEY = 'y'
WIDTH_KEY = 'width'
HEIGHT_KEY = 'height'

DEFAULTS = {
    DEFAULT_DOC_DIR_KEY: os.path.expanduser('~/Documents/'),
    DEFAULT_CSV_DIR_KEY: os.path.expanduser('~/Documents/'),
    POS_H_KEY: 222,
    POS_V_KEY: 130,
    WIDTH_KEY: 1080,
    HEIGHT_KEY: 700,
}

conf = None


def create_config():
    global conf
    if conf is None:
        conf = wx.FileConfig(APP_NAME, PUBLISHER_NAME)
    for k, v in DEFAULTS.items():
        if not conf.Exists(k):
            print(f'creating {k} -> {v}')
            if isinstance(v, int):
                conf.WriteInt(k, v)
            else:
                conf.Write(k, v)
        else:
            print(f'{k} = {conf.Read(k)}')
    conf.Flush()
