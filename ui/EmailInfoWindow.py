import wx

BORDER_SIZE = 5


class EmailInfoWindow(wx.Frame):
    def __init__(self, parent, title):
        super(EmailInfoWindow, self).__init__(parent, title=title, size=(600, 400))

        panel = wx.Panel(self)
        vbox = wx.BoxSizer(wx.VERTICAL)

        subject_tag = wx.StaticText(panel, -1, "Email Subject Line")

        vbox.Add(subject_tag, 0, wx.ALIGN_LEFT | wx.ALL, BORDER_SIZE)
        self.subject_text_ctrl = wx.TextCtrl(panel)

        vbox.Add(self.subject_text_ctrl, 0, wx.EXPAND | wx.ALIGN_LEFT | wx.ALL, BORDER_SIZE)
        self.subject_text_ctrl.SetMaxLength(200)
        self.subject_text_ctrl.Bind(wx.EVT_TEXT_MAXLEN, self.on_max_len)

        body_tag = wx.StaticText(panel, -1, "Email Body")
        vbox.Add(body_tag, 0, wx.EXPAND | wx.ALIGN_LEFT | wx.ALL, BORDER_SIZE)
        self.body_text_ctrl = wx.TextCtrl(panel, size=(500, 375), style=wx.TE_MULTILINE)
        self.body_text_ctrl.SetMaxLength(2)
        self.body_text_ctrl.Bind(wx.EVT_TEXT_MAXLEN, self.on_max_len)
        vbox.Add(self.body_text_ctrl, 1, wx.EXPAND | wx.ALIGN_LEFT | wx.ALL, BORDER_SIZE)

        button_panel = wx.Panel()
        button_box = wx.BoxSizer()
        # self.button_ok = wx.Button(button_panel, wx.ID_OK)
        # button_box.Add(self.button_ok)
        # self.Bind(wx.EVT_BUTTON, self.on_ok, self.button_ok)
        #
        # self.button_cancel = wx.Button(button_panel, wx.ID_CANCEL)
        # self.Bind(wx.EVT_BUTTON, self.on_cancel, self.button_cancel)
        # button_box.Add(self.button_cancel)
        #
        button_panel.SetSizer(button_box)
        vbox.Add(button_box)

        panel.SetSizer(vbox)

        self.Show()
        self.Fit()

    def on_max_len(self, event):
        print("Maximum length reached")

    def on_ok(self, event):
        print('ok')

    def on_cancel(self, event):
        print('cancel')
