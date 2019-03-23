import wx

import app_config


class FileMenu(wx.Menu):

    def __init__(self, parent_frame, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.parent_frame = parent_frame
        self.file_history = wx.FileHistory()
        self.file_history.Load(app_config.conf)

        item = self.Append(wx.ID_OPEN, "&Open...\tCtrl-O", "Open a ClassInvoices file")
        self.Bind(wx.EVT_MENU, self.parent_frame.on_open, item)
        self.add_recent_files()

        # --------------------
        self.AppendSeparator()

        item = self.Append(wx.ID_CLOSE, "&Close\tCtrl-W", "Close window and quit application")
        self.Bind(wx.EVT_MENU, self.parent_frame.on_close, item)

        item = self.Append(wx.ID_SAVE, "&Save\tCtrl-S", "Save the document")
        self.Bind(wx.EVT_MENU, self.parent_frame.on_save, item)
        item = self.Append(wx.ID_SAVEAS, "Save &As...\tCtrl-Alt-S", "Save the document as...")
        self.Bind(wx.EVT_MENU, self.parent_frame.on_save, item)

        # --------------------
        self.AppendSeparator()

        # Note: using ID_QUIT does not allow us to intercept the event to, for example, offer
        # to save the document. So, use ID_ANY instead :-(
        item = self.Append(wx.ID_ANY, "E&xit\tCtrl-Q", "Close this application")
        self.Bind(wx.EVT_MENU, self.parent_frame.on_quit, item)

    def add_recent_files(self):
        recent = wx.Menu()
        self.file_history.UseMenu(recent)
        self.file_history.AddFilesToMenu()
        recent.Bind(wx.EVT_MENU_RANGE, self.on_file_history, id=wx.ID_FILE1, id2=wx.ID_FILE9)
        self.AppendSubMenu(recent, "Open &Recent")

    def on_file_history(self, event=None):
        file_num = event.GetId() - wx.ID_FILE1
        path = self.file_history.GetHistoryFile(file_num)
        self.file_history.AddFileToHistory(path)  # move this one to the top of the list
        self.parent_frame.load_file(path)
