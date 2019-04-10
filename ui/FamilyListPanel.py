import wx

from model.columns import Column
from model.family import transform
from ui.ListSorterPanel import ListSorterPanel

DISPLAY_TRANSFORMS = {
    Column.CLASSES: lambda value: ', '.join(value),
}

COLUMN_DISPLAY_MAP = {
    Column.FAMILY_ID: 'Family ID',
    Column.REGISTERED: 'Register Date',
    Column.MEMBER_TYPE: 'Parent/Student',
    Column.LAST_NAME: 'Last Name',
    Column.FIRST_NAME: 'First Name',
    Column.EMAIL: 'E-mail Address',
    Column.PARENT_TYPE: 'Mother/Father',
    Column.PHONE: 'Phone',
    Column.BIRTHDAY: 'Birthday',
    Column.GENDER: 'Gender',
    Column.GRADE: 'Grade',
    Column.NOTES: 'Notes',
    Column.NEW_STUDENT: 'New?',
    Column.NONCONSECUTIVE: 'Nonconsecutive?',
    Column.CLASSES: 'Classes',
}


class FamilyListPanel(ListSorterPanel):
    def __init__(self, *args, **kwargs):
        ListSorterPanel.__init__(self, *args, **kwargs)
        self.SetMinSize((400, 100))

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.GetListCtrl(), proportion=1, flag=wx.EXPAND | wx.ALL, border=5)
        self.SetSizer(sizer)
        # self.Layout()

    def set_data(self, families):
        for col in Column:
            self.add_column(COLUMN_DISPLAY_MAP[col])
        for family in families.values():
            for person in family['students'] + family['parents']:
                row = []
                for col in Column:
                    col_value = transform(col, person[col], DISPLAY_TRANSFORMS)
                    row.append(col_value)
                self.add_row(row)
        self.SetColumnCount(len(COLUMN_DISPLAY_MAP))
        for c in range(len(COLUMN_DISPLAY_MAP)):
            self.resize_column(c)
        self.SortListItems(2)
        self.SortListItems(1)
