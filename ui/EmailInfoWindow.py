import wx

BORDER_SIZE = 5


class EmailInfoWindow(wx.Dialog):
    def __init__(self, parent, id=-1, title="Enter Name!"):
        wx.Dialog.__init__(self, parent, id, title, size=(-1, -1))

        self.mainSizer = wx.BoxSizer(wx.VERTICAL)
        self.buttonSizer = wx.BoxSizer(wx.HORIZONTAL)

        self.label = wx.StaticText(self, label="Enter Name:")
        self.field = wx.TextCtrl(self, value="", size=(300, 20))
        self.ok_button = wx.Button(self, label="OK", id=wx.ID_OK)
        self.cancel_button = wx.Button(self, label="Cancel", id=wx.ID_CANCEL)

        self.mainSizer.Add(self.label, 0, wx.ALL, 8)
        self.mainSizer.Add(self.field, 0, wx.ALL, 8)

        self.buttonSizer.Add(self.ok_button, 0, wx.ALL, 8)
        self.buttonSizer.Add(self.cancel_button, 0, wx.ALL, 8)

        self.mainSizer.Add(self.buttonSizer, 0, wx.ALL, 0)

        self.Bind(wx.EVT_BUTTON, self.on_ok, id=wx.ID_OK)
        self.Bind(wx.EVT_TEXT_ENTER, self.on_ok)

        self.Bind(wx.EVT_BUTTON, self.on_cancel, id=wx.ID_CANCEL)

        self.SetSizer(self.mainSizer)
        self.result = None

    def on_ok(self, event):
        print('ok')
        self.result = self.field.GetValue()
        self.Destroy()

    def on_cancel(self, event):
        print('cancel')
        self.result = None
        self.Destroy()
