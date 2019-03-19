import wx
from wx.lib.mixins import listctrl as listmix

import images
from ui.AutoWidthListCtrl import AutoWidthEditableListCtrl


# noinspection PyPep8Naming
class ListSorterPanel(wx.Panel, listmix.ColumnSorterMixin):

    def is_modified(self):
        return self.modified

    def GetListCtrl(self):
        return self.list_ctrl

    def GetSortImages(self):
        return self.sm_dn, self.sm_up

    def __init__(self, editable_columns=None, *args, **kwargs):
        """Create the main panel."""
        wx.Panel.__init__(self, *args, **kwargs)
        self.list_ctrl = AutoWidthEditableListCtrl(parent=self,
                                                   id=wx.ID_ANY,
                                                   editable_columns=editable_columns,
                                                   style=wx.LC_REPORT | wx.LC_SINGLE_SEL)

        #######################################################################
        # Set up column sorter mixin, which sorts table when column headers are clicked on
        self.itemDataMap = {}
        listmix.ColumnSorterMixin.__init__(self, 1)
        self.imageList = wx.ImageList(16, 16)
        self.sm_up = self.imageList.Add(images.SmallUpArrow.GetBitmap())
        self.sm_dn = self.imageList.Add(images.SmallDnArrow.GetBitmap())
        self.list_ctrl.SetImageList(self.imageList, wx.IMAGE_LIST_SMALL)

        self.columns = set()  # Column names
        self.column = []  # Columns of data
        self.modified = False

    def clear(self):
        self.list_ctrl.DeleteAllItems()
        self.list_ctrl.DeleteAllColumns()
        self.itemDataMap = {}
        self.columns = set()
        self.column = []

    def insert_item(self, row, value):
        self.list_ctrl.InsertItem(row, value)
        self.itemDataMap[row] = [value]
        self.list_ctrl.SetItemData(row, row)
        self.column[0].add(value)

    def set_item(self, row, col, value):
        self.list_ctrl.SetItem(row, col, str(value))
        self.column[col].add(value)
        if row in self.itemDataMap and col < len(self.itemDataMap[row]):
            self.itemDataMap[row][col] = value
        else:
            self.itemDataMap[row].append(value)

    def add_row(self, row, dedup_col=None):
        row_num = self.list_ctrl.GetItemCount()
        if dedup_col is not None:
            if row[dedup_col] in self.column[dedup_col]:
                return
        self.insert_item(row_num, row[0])
        for col_num in range(1, len(row)):
            self.set_item(row_num, col_num, row[col_num])

    def resize_column(self, col):
        self.list_ctrl.SetColumnWidth(col, wx.LIST_AUTOSIZE_USEHEADER)

    def add_column(self, col_name, **kwargs):
        if col_name not in self.columns:
            self.list_ctrl.InsertColumn(len(self.columns), col_name, **kwargs)
            self.columns.add(col_name)
            self.column.append(set())
