import wx

import app_config


class FileMenu(wx.Menu):

    def __init__(self, parent_frame, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.parent_frame = parent_frame
        self.file_history = wx.FileHistory()

        item = self.Append(wx.ID_OPEN, "&Open...\tCtrl-O", "Open a ClientInvoices file")
        self.Bind(wx.EVT_MENU, self.on_open, item)

        # --------------------
        self.AppendSeparator()

        item = self.Append(wx.ID_CLOSE, "&Close\tCtrl-W", "Close window and quit application")
        self.Bind(wx.EVT_MENU, self.on_quit, item)

        item = self.Append(wx.ID_SAVE, "&Save\tCtrl-S", "Save the document")
        self.Bind(wx.EVT_MENU, self.on_save, item)

        # --------------------
        self.AppendSeparator()
        # self.add_recent_files()

        # --------------------
        self.AppendSeparator()

        # Note: using ID_QUIT does not allow us to intercept the event to, for example, offer
        # to save the document. So, use ID_ANY instead :-(
        item = self.Append(wx.ID_ANY, "E&xit\tCtrl-Q", "Close this application")
        self.Bind(wx.EVT_MENU, self.on_quit, item)

    def on_quit(self, event=None):
        """Exit application."""
        self.parent_frame.on_close()

    def on_open(self, event=None):
        """Exit application."""
        print(event)
        self.parent_frame.on_open()

    def on_save(self, event=None):
        """Exit application."""
        self.parent_frame.on_save()

    def add_recent_files(self):
        recent_files = app_config.conf.get(app_config.RECENT_FILES_KEY)
        if recent_files:
            for file in recent_files:
                self.file_history.AddFileToHistory(file)
                self.file_history.AddFilesToMenu()
            self.file_history.AddFilesToMenu(menu=self)
            # self.Bind(wx.EVT_MENU, self.on_open, file_menu)
            # self.Append(wx.ID_ANY, "Open Recent", sub_menu)
