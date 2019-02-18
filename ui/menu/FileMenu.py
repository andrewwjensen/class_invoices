import wx


class FileMenu(wx.Menu):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        item = self.Append(wx.ID_EXIT, "&Open")
        self.Bind(wx.EVT_MENU, self.on_open, item)

        self.AppendSeparator()

        item = self.Append(wx.ID_EXIT, "&Quit")
        self.Bind(wx.EVT_MENU, self.on_quit, item)

    def on_open(self, event=None):
        """Open a new CSV file."""
        print(event)

    def on_quit(self, event=None):
        """Exit application."""
        self.parent.Close()
