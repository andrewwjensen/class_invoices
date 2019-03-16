#!/usr/bin/env python3

import wx

import app_config
import ui.MainFrame


def main():
    app = wx.App()
    frame = ui.MainFrame(None,
                         title=app_config.APP_NAME,
                         size=(1080, 700))
    # frame.Maximize()
    # frame.set_splitter_width()
    frame.Show()
    app.MainLoop()


if __name__ == '__main__':
    main()
