import wx


class HelpMenu(wx.Menu):
    def __init__(self, parent, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.parent = parent

        menu_about = self.Append(wx.ID_ABOUT, "&About ClassInvoices", "About ClassInvoices")
        self.Bind(wx.EVT_MENU, self.on_about, menu_about)

    def on_about(self, event=None):
        # A message dialog box with an OK button. wx.OK is a standard ID in wxWidgets.
        dlg = wx.MessageDialog(self, "A small text editor", "About Sample Editor", wx.OK)
        dlg.ShowModal()  # Show it
        dlg.Destroy()  # finally destroy it when finished.
