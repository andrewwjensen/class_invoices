import csv
import datetime
import os

import wx
import wx.lib.mixins.listctrl as listmix

import images

NONCONSECUTIVE_COL = 'is_nonconsecutive'
NEW_STUDENT_COL = 'is_new_student'
NOTES_COL = 'notes'
GRADE_COL = 'grade'
GENDER_COL = 'gender'
BIRTHDAY_COL = 'birth_date'
PHONE_COL = 'phone'
PARENT_TYPE_COL = 'parent_type'
EMAIL_COL = 'email'
MEMBER_TYPE_COL = 'member_type'
REGISTERED_COL = 'registered_at'
CLASSES_COL = 'classes'
FIRST_NAME_COL = 'first_name'
LAST_NAME_COL = 'last_name'
FAMILY_ID_COL = 'family_id'

COLUMN_MAP = {
    FAMILY_ID_COL: 'Family ID',
    REGISTERED_COL: 'Register Date',
    MEMBER_TYPE_COL: 'Parent/Student',
    LAST_NAME_COL: 'Last Name',
    FIRST_NAME_COL: 'First Name',
    EMAIL_COL: 'E-mail Address',
    PARENT_TYPE_COL: 'Mother/Father',
    PHONE_COL: 'Phone',
    BIRTHDAY_COL: 'Birthday',
    GENDER_COL: 'Gender',
    GRADE_COL: 'Grade',
    NOTES_COL: 'Notes',
    NEW_STUDENT_COL: 'New?',
    NONCONSECUTIVE_COL: 'Nonconsecutive?',
    CLASSES_COL: 'Classes',
}

VALID_MEMBER_TYPES = ['parent', 'student']
VALID_PARENT_TYPES = ['mother', 'father']
VALID_GENDERS = ['male', 'female']

DISPLAY_COLUMNS = [
    FAMILY_ID_COL,
    LAST_NAME_COL,
    FIRST_NAME_COL,
    CLASSES_COL,
]


# DISPLAY_COLUMNS = COLUMN_MAP.keys()


def parse_bool(bool_str):
    if bool_str is None:
        return False
    val = bool_str.strip().lower()
    return val not in ['', 'no', 'n', 'false', 'f', '0']


def parse_date(date_str):
    try:
        return datetime.datetime.strptime(date_str, '%m/%d/%Y %H:%M')
    except ValueError:
        return date_str


def parse_list(list_str):
    """Parse comma-separated list"""
    if list_str.strip():
        return [t.strip() for t in list_str.split(',') if t.strip()]
    else:
        return []


PARSE_TRANSFORMS = {
    NEW_STUDENT_COL: lambda value: parse_bool(value),
    NONCONSECUTIVE_COL: lambda value: parse_bool(value),
    CLASSES_COL: lambda value: parse_list(value),
    REGISTERED_COL: lambda value: parse_date(value),
    BIRTHDAY_COL: lambda value: parse_date(value),
}

DISPLAY_TRANSFORMS = {
    CLASSES_COL: lambda value: ', '.join(value),
}


def transform(col_name, value, transforms):
    try:
        transform_func = transforms[col_name]
    except KeyError:
        return value
    return transform_func(value)


class AutoWidthListCtrl(wx.ListCtrl, listmix.ListCtrlAutoWidthMixin):
    def __init__(self, parent, wx_id, pos=wx.DefaultPosition,
                 size=wx.DefaultSize, style=0):
        wx.ListCtrl.__init__(self, parent, wx_id, pos, size, style)
        listmix.ListCtrlAutoWidthMixin.__init__(self)


class AutoWidthEditableListCtrl(wx.ListCtrl, listmix.ListCtrlAutoWidthMixin, listmix.TextEditMixin):
    def __init__(self, parent, wx_id,
                 editable_columns=None,
                 pos=wx.DefaultPosition,
                 size=wx.DefaultSize, style=0):
        wx.ListCtrl.__init__(self, parent, wx_id, pos, size, style)
        listmix.ListCtrlAutoWidthMixin.__init__(self)
        listmix.TextEditMixin.__init__(self)
        print(editable_columns)
        self.editable_columns = editable_columns
        if editable_columns is None:
            self.editable_columns = []

    def OpenEditor(self, col, row):
        print(col, self.editable_columns)
        if col in self.editable_columns:
            listmix.TextEditMixin.OpenEditor(self, col, row)


def validate_person(person):
    if person[MEMBER_TYPE_COL] and person[MEMBER_TYPE_COL] not in VALID_MEMBER_TYPES:
        raise RuntimeError("Invalid person: bad " + MEMBER_TYPE_COL +
                           " column. Got '" + person[MEMBER_TYPE_COL] +
                           "'. Valid member types: " + ', '.join(VALID_MEMBER_TYPES))
    elif person[PARENT_TYPE_COL] and person[PARENT_TYPE_COL] not in VALID_PARENT_TYPES:
        raise RuntimeError("Invalid person: bad " + PARENT_TYPE_COL +
                           " column. Got '" + person[PARENT_TYPE_COL] +
                           "'. Valid parent types: " + ', '.join(VALID_PARENT_TYPES))
    elif person[GENDER_COL] and person[GENDER_COL] not in VALID_GENDERS:
        raise RuntimeError("Invalid person: bad " + GENDER_COL +
                           " column. Got '" + person[GENDER_COL] +
                           "'. Valid parent types: " + ', '.join(VALID_GENDERS))


def display_filter(person):
    return person[MEMBER_TYPE_COL] == 'student'


def validate_header_row(row):
    missing_columns = []
    for column in DISPLAY_COLUMNS:
        if column not in row:
            missing_columns.append(column)
    if missing_columns:
        raise RuntimeError("Missing required columns: "
                           + ', '.join(missing_columns))


def get_parents(family):
    return [person for person in family if person[MEMBER_TYPE_COL] == 'parent']


def get_students(family):
    return [person for person in family if person[MEMBER_TYPE_COL] != 'parent']


class ListSorterPanel(wx.Panel, listmix.ColumnSorterMixin):
    def GetListCtrl(self):
        return self.list_ctrl

    def GetSortImages(self):
        return self.sm_dn, self.sm_up

    def __init__(self, parent, my_id, listctl_class, editable_columns=None,
                 *args, **kwargs):
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
        self.list_ctrl.SetItem(row, col, value)
        if row in self.itemDataMap and col < len(self.itemDataMap[row]):
            self.itemDataMap[row][col] = value
        else:
            self.itemDataMap[row].append(value)

    def SetColumnWidth(self, col, sz):
        self.list_ctrl.SetColumnWidth(col, sz)

    def InsertColumn(self, col, info):
        self.list_ctrl.InsertColumn(col, info)


class DataPanel(wx.Panel):
    """This Panel holds the main application data, a table of CSV values."""

    def __init__(self, parent, my_id, *args, **kwargs):
        """Create the main panel."""
        wx.Panel.__init__(self, parent, my_id, *args, **kwargs)

        self.headers = []
        self.classes = set()
        self.column_name_to_idx = {}
        self.column_idx_to_name = {}
        self.families = {}
        self.parent = parent

        #######################################################################
        # Create splitter window and its two horizontal panels
        self.splitter = wx.SplitterWindow(self, wx.ID_ANY, style=wx.SP_3DBORDER | wx.SP_3D)
        self.student_panel = ListSorterPanel(self.splitter, wx.ID_ANY, AutoWidthListCtrl)
        self.fee_panel = ListSorterPanel(self.splitter, wx.ID_ANY, AutoWidthEditableListCtrl, editable_columns=[2])
        self.splitter.SplitVertically(self.student_panel, self.fee_panel)

        #######################################################################
        # Populate student panel (left)
        self.student_panel.SetMinSize((400, 100))

        # Create student panel buttons
        self.button_generate = wx.Button(self.student_panel, wx.ID_ANY, "Generate Invoices...")
        self.Bind(wx.EVT_BUTTON, self.on_generate, self.button_generate)
        self.button_generate.Disable()

        student_buttons_sizer = wx.BoxSizer(wx.HORIZONTAL)
        student_buttons_sizer.Add(self.button_generate, 0, wx.ALIGN_CENTER_HORIZONTAL | wx.ALIGN_CENTER_VERTICAL)

        student_table_sizer = wx.BoxSizer(wx.VERTICAL)
        student_table_sizer.Add(self.student_panel.GetListCtrl(), 1, wx.EXPAND, 0)
        student_table_sizer.Add(student_buttons_sizer, 0, wx.EXPAND)
        self.student_panel.SetSizer(student_table_sizer)

        #######################################################################
        # Populate fee schedule panel (right)
        self.fee_panel.SetMinSize((200, 100))

        # Create fee schedule panel buttons
        self.button_import = wx.Button(self.fee_panel, wx.ID_ANY, "Import Class Fees...")
        self.Bind(wx.EVT_BUTTON, self.on_import, self.button_import)
        self.button_import.Disable()

        fee_buttons_sizer = wx.BoxSizer(wx.HORIZONTAL)
        fee_buttons_sizer.Add(self.button_import, 0, wx.ALIGN_CENTER_HORIZONTAL | wx.ALIGN_CENTER_VERTICAL)

        fee_table_sizer = wx.BoxSizer(wx.VERTICAL)
        fee_table_sizer.Add(self.fee_panel.GetListCtrl(), 1, wx.EXPAND, 0)
        fee_table_sizer.Add(fee_buttons_sizer, 0, wx.EXPAND)
        self.fee_panel.SetSizer(fee_table_sizer)

        # Add the splitter to a sizer and do the layout to pull everything together
        box_outer = wx.BoxSizer(wx.VERTICAL)
        box_outer.Add(self.splitter, 1, wx.EXPAND)
        self.SetAutoLayout(True)
        self.SetSizer(box_outer)
        box_outer.SetSizeHints(self)
        self.Layout()
        self.Bind(wx.EVT_KEY_DOWN, self.on_keypress)

    def on_keypress(self, event=None):
        print("event:", event)

    def set_data(self, data):
        self.clear_data()
        row_num = 0
        try:
            for row in data:
                if self.headers is None:
                    # This is the first row, map columns
                    self.process_header_row(row)
                else:
                    row_num = self.process_data_row(row_num, row)
            self.button_generate.Enable()
            self.button_import.Enable()

            # Update ColumnSorterMixin column count
            self.student_panel.SetColumnCount(len(self.headers))
            self.student_panel.SortListItems(1)

            self.process_classes()

        except RuntimeError as e:
            self.clear_data()
            dlg = wx.MessageDialog(self, str(e), "Warning", wx.OK | wx.CANCEL)
            dlg.ShowModal()
            dlg.Destroy()

    def clear_data(self):
        self.headers = None
        self.classes = set()
        self.families = {}
        self.button_generate.Disable()
        self.button_import.Disable()
        self.student_panel.clear()
        self.fee_panel.clear()

    def process_header_row(self, row):
        self.column_name_to_idx = {}
        self.column_idx_to_name = {}
        display_row = []
        for n, header in enumerate(row):
            self.column_idx_to_name[n] = header
            self.column_name_to_idx[header] = n
        validate_header_row(row)
        for n, header in enumerate(DISPLAY_COLUMNS):
            display_header = COLUMN_MAP[row[self.column_name_to_idx[header]]]
            self.student_panel.InsertColumn(n, display_header)
            display_row.append(display_header)
        self.headers = display_row

    def process_data_row(self, row_num, row):
        person = self.create_person(row)
        self.add_to_family(person)
        for class_name in person[CLASSES_COL]:
            self.classes.add(class_name)
        if display_filter(person):
            for c, column in enumerate(DISPLAY_COLUMNS):
                col_value = transform(column, person[column], DISPLAY_TRANSFORMS)
                if c == 0:
                    self.student_panel.InsertItem(row_num, col_value)
                else:
                    self.student_panel.SetItem(row_num, c, col_value)
                self.student_panel.SetColumnWidth(c, wx.LIST_AUTOSIZE_USEHEADER)
            row_num += 1
        return row_num

    def add_to_family(self, person):
        family_id = person[FAMILY_ID_COL]
        try:
            # print('adding to family {famid}: {person}'.format(famid=family_id, person=person))
            self.families[family_id].append(person)
        except KeyError:
            # print('creating family {famid}: {person}'.format(famid=family_id, person=person))
            self.families[family_id] = [person]

    def create_person(self, row):
        person = {}
        for n, column in enumerate(row):
            col_name = self.column_idx_to_name[n]
            person[col_name] = column
        for col_name, value in person.items():
            person[col_name] = transform(col_name, value, PARSE_TRANSFORMS)
        validate_person(person)
        return person

    def process_classes(self):
        self.fee_panel.InsertColumn(0, 'Class')
        self.fee_panel.InsertColumn(1, 'Teacher')
        self.fee_panel.InsertColumn(2, 'Fee')
        for n, class_name in enumerate(sorted(self.classes)):
            self.fee_panel.InsertItem(n, class_name)
            # Add blank data values for the 2nd and 3rd columns
            self.fee_panel.SetItem(n, 1, '')
            self.fee_panel.SetItem(n, 2, '')
        self.fee_panel.SetColumnWidth(0, wx.LIST_AUTOSIZE_USEHEADER)
        # Update ColumnSorterMixin column count
        self.fee_panel.SetColumnCount(3)
        self.fee_panel.SortListItems(0)

    def on_generate(self, event=None):
        for family_id, family in self.families.items():
            self.create_invoice(family)

    def on_import(self, event=None):
        dirname = ''
        file_dialog = wx.FileDialog(parent=self.parent,
                                    message="Choose a fee schedule file",
                                    defaultDir=dirname,
                                    defaultFile="",
                                    wildcard="*.csv",
                                    style=wx.FD_OPEN)
        if file_dialog.ShowModal() == wx.ID_OK:
            filename = file_dialog.GetFilename()
            dirname = file_dialog.GetDirectory()
            rows = []
            with open(os.path.join(dirname, filename), 'r') as f:
                reader = csv.reader(f)
                for row in reader:
                    rows.append(row)
            self.process_fee_schedule_file(rows)
        file_dialog.Destroy()

    def create_invoice(self, family):
        parents = get_parents(family)
        students = get_students(family)
        print('======================')
        for parent in parents:
            print('{:30}  {}'.format(
                parent[LAST_NAME_COL] + ', ' + parent[FIRST_NAME_COL], parent[EMAIL_COL]))
        for student in students:
            print('  {:28}'.format(student[LAST_NAME_COL] + ', ' + student[FIRST_NAME_COL]))

    def process_fee_schedule_file(self, fee_schedule_rows):
        lookup = {entry[0]: entry for entry in fee_schedule_rows}
        missing_classes = []
        for n, class_name in enumerate(self.classes):
            try:
                entry = lookup[class_name]
                self.fee_panel.SetItem(n, 1, entry[1])
                self.fee_panel.SetItem(n, 2, entry[2])
            except KeyError:
                missing_classes.append(class_name)
        self.fee_panel.SetColumnWidth(1, wx.LIST_AUTOSIZE_USEHEADER)
        self.fee_panel.SetColumnWidth(2, wx.LIST_AUTOSIZE_USEHEADER)
        self.fee_panel.Refresh()
        if missing_classes:
            msg = 'Missing classes:\n  ' + '\n  '.join(missing_classes)
            dlg = wx.MessageDialog(self, msg, "Error", wx.OK)
            dlg.ShowModal()
            dlg.Destroy()
        else:
            for cl in self.classes:
                print(cl)
