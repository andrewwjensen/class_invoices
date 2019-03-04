import wx

import app_config
from ui.MainFrame import MainFrame


def main():
    app = wx.App()
    frame = MainFrame(None,
                      title=app_config.APP_NAME,
                      size=(500, 400))
    frame.Maximize()
    frame.set_splitter_width()
    frame.Show()
    app.MainLoop()


if __name__ == '__main__':
    main()
