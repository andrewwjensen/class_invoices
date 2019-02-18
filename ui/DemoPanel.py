import wx


class DemoPanel(wx.Panel):
    """This Panel hold two simple buttons, but doesn't really do anything."""

    def __init__(self, parent, *args, **kwargs):
        """Create the DemoPanel."""
        wx.Panel.__init__(self, parent, *args, **kwargs)

        self.parent = parent  # Sometimes one can use inline Comments

        nothing_btn = wx.Button(self, label="Do Nothing with a long label")
        nothing_btn.Bind(wx.EVT_BUTTON, self.do_nothing)

        msg_btn = wx.Button(self, label="Send Message")
        msg_btn.Bind(wx.EVT_BUTTON, self.on_message_button)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(nothing_btn, 0, wx.ALIGN_CENTER | wx.ALL, 5)
        sizer.Add(msg_btn, 0, wx.ALIGN_CENTER | wx.ALL, 5)

        self.SetSizerAndFit(sizer)

    def do_nothing(self, event=None):
        """Do nothing."""
        pass

    def on_message_button(self, event=None):
        """Bring up a wx.MessageDialog with a useless message."""
        dlg = wx.MessageDialog(self,
                               message='A completely useless message',
                               caption='A Message Box',
                               style=wx.OK | wx.ICON_INFORMATION
                               )
        dlg.ShowModal()
        dlg.Destroy()
