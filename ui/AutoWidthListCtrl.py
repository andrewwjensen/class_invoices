import wx
from wx.lib.mixins import listctrl as listmix


class AutoWidthListCtrl(wx.ListCtrl, listmix.ListCtrlAutoWidthMixin):
    def __init__(self, parent, wx_id, pos=wx.DefaultPosition, size=wx.DefaultSize, style=0):
        wx.ListCtrl.__init__(self, parent, wx_id, pos, size, style)
        listmix.ListCtrlAutoWidthMixin.__init__(self)


class AutoWidthEditableListCtrl(wx.ListCtrl,
                                listmix.ListCtrlAutoWidthMixin,
                                listmix.TextEditMixin):
    def __init__(self, parent, wx_id, editable_columns=None, pos=wx.DefaultPosition, size=wx.DefaultSize, style=0):
        wx.ListCtrl.__init__(self, parent, wx_id, pos, size, style)
        listmix.ListCtrlAutoWidthMixin.__init__(self)
        listmix.TextEditMixin.__init__(self)
        self.editable_columns = editable_columns
        if editable_columns is None:
            self.editable_columns = []
        self.modified = False
        self.value_save = None

    def is_modified(self):
        return self.modified

    def OpenEditor(self, col, row):
        if col in self.editable_columns:
            self.value_save = self.GetItem(row, col).GetText()
            listmix.TextEditMixin.OpenEditor(self, col, row)

    def CloseEditor(self, event=None):
        if not self.editor.IsShown():
            return
        new_value = self.editor.GetValue()
        if new_value != self.value_save:
            self.modified = True
        listmix.TextEditMixin.CloseEditor(self)
