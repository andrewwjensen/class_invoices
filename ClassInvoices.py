#!/usr/bin/env python3

import wx

import app_config
import ui.MainFrame


def main():
    app = wx.App()
    app_config.create_config()
    cfg = app_config.conf
    frame = ui.MainFrame(None,
                         title=app_config.APP_NAME,
                         size=(cfg.ReadInt(app_config.WIDTH_KEY),
                               cfg.ReadInt(app_config.HEIGHT_KEY)))
    frame.Show()
    app.MainLoop()


if __name__ == '__main__':
    main()
