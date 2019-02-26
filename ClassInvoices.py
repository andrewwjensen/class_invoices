import wx

from ui.MainFrame import MainFrame


def main():
    app = wx.App()
    frame = MainFrame(None, title="Micro App", size=(500, 400))
    frame.Show()
    app.MainLoop()


if __name__ == '__main__':
    main()
