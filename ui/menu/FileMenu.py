import os

import wx


class FileMenu(wx.Menu):

    def __init__(self, parent, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.parent = parent
        self.content = None

        item = self.Append(wx.ID_OPEN, "&Open FIle...\tCtrl-O", "Open new CSV file")
        self.Bind(wx.EVT_MENU, self.on_open, item)
        item = self.Append(wx.ID_CLOSE, "&Close\tCtrl-W", "Close window and quit application")
        self.Bind(wx.EVT_MENU, self.on_quit, item)

        self.AppendSeparator()

        item = self.Append(wx.ID_EXIT, "E&xit\tCtrl-Q", "Close this application")
        self.Bind(wx.EVT_MENU, self.on_quit, item)

    def on_open(self, event=None):
        """Open a new CSV file."""
        dirname = ''
        file_dialog = wx.FileDialog(parent=self.parent,
                                    message="Choose a file",
                                    defaultDir=dirname,
                                    defaultFile="",
                                    wildcard="*.*",
                                    style=wx.FD_OPEN)
        if file_dialog.ShowModal() == wx.ID_OK:
            filename = file_dialog.GetFilename()
            dirname = file_dialog.GetDirectory()
            with open(os.path.join(dirname, filename), 'r') as f:
                self.content = f.read()
        file_dialog.Destroy()

    def on_quit(self, event=None):
        """Exit application."""
        self.parent.Close()
