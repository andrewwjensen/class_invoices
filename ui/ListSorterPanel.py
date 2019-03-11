import wx
from wx.lib.mixins import listctrl as listmix

import images


# noinspection PyPep8Naming
class ListSorterPanel(wx.Panel, listmix.ColumnSorterMixin):
    def GetListCtrl(self):
        return self.list_ctrl

    def GetSortImages(self):
        return self.sm_dn, self.sm_up

    def __init__(self, parent, my_id, listctl_class, editable_columns=None, *args, **kwargs):
        """Create the main panel."""
        wx.Panel.__init__(self, parent, my_id, *args, **kwargs)
        if editable_columns is not None:
            kwargs['editable_columns'] = editable_columns
        self.list_ctrl = listctl_class(self, wx.ID_ANY,
                                       style=wx.LC_REPORT | wx.LC_SINGLE_SEL,
                                       size=(1, 150),
                                       **kwargs)
        self.editable_columns = editable_columns

        #######################################################################
        # Set up column sorter mixin, which sorts table when column headers are clicked on
        self.itemDataMap = {}
        listmix.ColumnSorterMixin.__init__(self, 1)
        self.imageList = wx.ImageList(16, 16)
        self.sm_up = self.imageList.Add(images.SmallUpArrow.GetBitmap())
        self.sm_dn = self.imageList.Add(images.SmallDnArrow.GetBitmap())
        self.list_ctrl.SetImageList(self.imageList, wx.IMAGE_LIST_SMALL)

    def clear(self):
        self.list_ctrl.DeleteAllItems()
        self.list_ctrl.DeleteAllColumns()
        self.itemDataMap = {}

    def InsertItem(self, row, value):
        self.list_ctrl.InsertItem(row, value)
        self.itemDataMap[row] = [value]
        self.list_ctrl.SetItemData(row, row)

    def SetItem(self, row, col, value):
        self.list_ctrl.SetItem(row, col, str(value))
        if row in self.itemDataMap and col < len(self.itemDataMap[row]):
            self.itemDataMap[row][col] = value
        else:
            self.itemDataMap[row].append(value)

    def SetColumnWidth(self, col, sz):
        self.list_ctrl.SetColumnWidth(col, sz)

    def InsertColumn(self, col, info):
        self.list_ctrl.InsertColumn(col, info)
