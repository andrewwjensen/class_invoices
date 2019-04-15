#!/usr/bin/env python3
import logging
import logging.config
import os

import wx
import yaml

import app_config

ATTRIBUTION = 'Icon made by Freepik from www.flaticon.com'


def setup_logging(
    default_path='logging.yaml',
    default_level=logging.INFO,
    env_key='LOG_CFG'
):
    """Setup logging configuration
    """
    path = default_path
    value = os.getenv(env_key, None)
    if value:
        path = value
    if os.path.exists(path):
        with open(path, 'rt') as f:
            config = yaml.safe_load(f.read())
        logging.config.dictConfig(config)
    else:
        logging.basicConfig(format='%(asctime)s %(levelname)-8s %(message)s',
                            level=default_level)


def main():
    app = wx.App()
    app_config.create_config()
    setup_logging()

    # Need this import after setting up logging
    import ui.MainFrame
    frame = ui.MainFrame(None,
                         title=app_config.APP_NAME,
                         size=(1080, 700))
    frame.Show()
    app.MainLoop()


if __name__ == '__main__':
    main()
