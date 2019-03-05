import csv
import os

import wx

import app_config


class FileMenu(wx.Menu):

    def __init__(self, parent, data_panel, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.parent = parent
        self.data_panel = data_panel

        item = self.Append(wx.ID_OPEN, "&Open...\tCtrl-O", "Open new CSV file")
        self.Bind(wx.EVT_MENU, self.on_open, item)
        self.add_recent_files()

        item = self.Append(wx.ID_CLOSE, "&Close\tCtrl-W", "Close window and quit application")
        self.Bind(wx.EVT_MENU, self.on_quit, item)

        # --------------------
        self.AppendSeparator()

        item = self.Append(wx.ID_EXIT, "E&xit\tCtrl-Q", "Close this application")
        self.Bind(wx.EVT_MENU, self.on_quit, item)

    def on_open(self, event=None):
        """Open a new CSV file."""
        dirname = ''
        file_dialog = wx.FileDialog(parent=self.parent,
                                    message="Choose a registration CSV file",
                                    defaultDir=dirname,
                                    defaultFile="",
                                    wildcard="*.CSV",
                                    style=wx.FD_OPEN)
        if file_dialog.ShowModal() == wx.ID_OK:
            filename = file_dialog.GetFilename()
            dirname = file_dialog.GetDirectory()
            path = os.path.join(dirname, filename)
            self.data_panel.load_students(path)
        file_dialog.Destroy()

    def on_quit(self, event=None):
        """Exit application."""
        self.parent.Close()

    def add_recent_files(self):
        recent_files = app_config.conf.get(app_config.RECENT_FILES_KEY)
        if recent_files:
            sub_menu = wx.Menu()
            for file in recent_files:
                sub_menu.Append(wx.ID_ANY, file)
            self.Append(wx.ID_ANY, "Recent files")
