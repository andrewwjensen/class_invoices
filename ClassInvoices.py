#!/usr/bin/env python3

import wx

import app_config
import ui.MainFrame


def main():
    app = wx.App()
    app_config.create_config()
    frame = ui.MainFrame(None,
                         title=app_config.APP_NAME,
                         size=(1080, 700),
                         )
    frame.Show()
    app.MainLoop()


if __name__ == '__main__':
    main()
