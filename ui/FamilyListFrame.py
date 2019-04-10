import wx

from ui.FamilyListPanel import FamilyListPanel


class FamilyListFrame(wx.Frame):
    def __init__(self, *args, **kw):
        super().__init__(*args, **kw)

        self.SetSize((1000, 800))
        self.family_panel = FamilyListPanel(parent=self)

    def set_families(self, families):
        self.family_panel.set_data(families)
