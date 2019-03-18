import wx


class EditMenu(wx.Menu):

    def __init__(self, parent, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.parent = parent

        cut = self.Append(wx.ID_ANY, '&Cut\tCtrl+X', 'Cut the Selection')
        cut.Enable(False)
        copy = self.Append(wx.ID_ANY, '&Copy\tCtrl+C', 'Copy the Selection')
        self.Bind(wx.EVT_MENU, self.on_copy, copy)
        paste = self.Append(wx.ID_ANY, '&Paste\tCtrl+V', 'Paste text from clipboard')
        self.Bind(wx.EVT_MENU, self.on_copy, paste)
        delete = self.Append(wx.ID_ANY, '&Delete', 'Delete the selected text')
        self.Bind(wx.EVT_MENU, self.on_copy, delete)
        # --------------------
        self.AppendSeparator()
        self.Append(wx.ID_ANY, 'Select &All\tCtrl+A', 'Select the entire text')

    def on_copy(self, event=None):
        """Exit application."""
        self.parent.copy()
