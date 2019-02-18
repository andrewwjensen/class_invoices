import wx
import app_config

from ui.MainFrame import MainFrame

PUBLISHER_Name = 'AndyJensen'
APP_NAME = 'ClassInvoices'


def main():
    global conf
    conf = app_config.Config(PUBLISHER_Name, APP_NAME)
    conf.get_config(app_config.RECENT_FILES_KEY, str)
    app = wx.App()
    frame = MainFrame(None, title="Micro App", size=(500, 400))
    frame.Show()
    app.MainLoop()


if __name__ == '__main__':
    main()
