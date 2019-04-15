#!/usr/bin/env python3
import logging

import wx

import app_config

ATTRIBUTION = 'Icon made by Freepik from www.flaticon.com'

logging.basicConfig(format='%(asctime)s %(levelname)-8s %(message)s')
logging.getLogger(app_config.APP_NAME).setLevel(logging.INFO)


def main():
    app = wx.App()
    app_config.create_config()

    # Need this import after setting up logging
    import ui.MainFrame
    frame = ui.MainFrame(None,
                         title=app_config.APP_NAME,
                         size=(1080, 700))
    frame.Show()
    app.MainLoop()


if __name__ == '__main__':
    main()
