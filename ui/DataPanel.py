import datetime

import wx
from wx.lib.printout import PrintTable
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


PARSE_TRANSFORMS = {
    NEW_STUDENT_COL: lambda value: parse_bool(value),
    NONCONSECUTIVE_COL: lambda value: parse_bool(value),
    CLASSES_COL: lambda value: [t.strip() for t in value.split(',')],
    REGISTERED_COL: lambda value: parse_date(value),
    BIRTHDAY_COL: lambda value: parse_date(value),
}

DISPLAY_TRANSFORMS = {
    CLASSES_COL: lambda value: ', '.join(value),
}


# DISPLAY_COLUMNS = COLUMN_MAP.keys()


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


class DataPanel(wx.Panel, listmix.ColumnSorterMixin):
    """This Panel holds the main application data, a table of CSV values."""

    def GetListCtrl(self):
        return self.student_list

    def GetSortImages(self):
        return self.sm_dn, self.sm_up

    def __init__(self, parent, my_id, *args, **kwargs):
        """Create the main panel."""
        wx.Panel.__init__(self, parent, my_id, *args, **kwargs)

        self.headers = []
        self.rows = []
        self.classes = set()
        self.column_name_to_idx = {}
        self.column_idx_to_name = {}
        self.families = {}
        self.parent = parent

        self.student_list = AutoWidthListCtrl(self, wx.ID_ANY,
                                              style=wx.LC_REPORT | wx.LC_SINGLE_SEL,
                                              size=(1, 150))
        self.fee_list = AutoWidthListCtrl(self, wx.ID_ANY,
                                          style=wx.LC_REPORT | wx.LC_SINGLE_SEL,
                                          size=(1, 150))

        self.itemDataMap = {}
        listmix.ColumnSorterMixin.__init__(self, len(DISPLAY_COLUMNS))
        self.imageList = wx.ImageList(16, 16)
        self.sm_up = self.imageList.Add(images.SmallUpArrow.GetBitmap())
        self.sm_dn = self.imageList.Add(images.SmallDnArrow.GetBitmap())
        self.student_list.SetImageList(self.imageList, wx.IMAGE_LIST_SMALL)

        self.button_print = wx.Button(self, wx.ID_ANY, "Print Master List...")
        self.Bind(wx.EVT_BUTTON, self.on_print, self.button_print)
        self.button_print.Disable()
        self.button_generate = wx.Button(self, wx.ID_ANY, "Generate Invoices...")
        self.Bind(wx.EVT_BUTTON, self.on_generate, self.button_generate)
        self.button_generate.Disable()

        self.__do_layout()

    def __do_layout(self):
        box_data = wx.BoxSizer(wx.HORIZONTAL)

        box_student_table = wx.BoxSizer(wx.VERTICAL)
        box_student_table.Add(self.student_list, 1, wx.EXPAND | wx.ALL, 5)
        box_data.Add(box_student_table, 2, wx.EXPAND)

        box_fee_table = wx.BoxSizer(wx.VERTICAL)
        box_fee_table.Add(self.fee_list, 1, wx.EXPAND | wx.ALL, 5)
        box_data.Add(box_fee_table, 1, wx.EXPAND)

        box_buttons = wx.BoxSizer(wx.HORIZONTAL)
        box_buttons.Add(self.button_print, 0, wx.ALIGN_CENTER_HORIZONTAL | wx.ALIGN_CENTER_VERTICAL)
        box_buttons.Add(self.button_generate, 0, wx.ALIGN_CENTER_HORIZONTAL | wx.ALIGN_CENTER_VERTICAL)

        box_outer = wx.BoxSizer(wx.VERTICAL)
        box_outer.Add(box_data, 1, wx.EXPAND)
        box_outer.Add(box_buttons, 0, wx.EXPAND)

        self.SetAutoLayout(True)
        self.SetSizer(box_outer)
        box_outer.Fit(self)
        box_outer.SetSizeHints(self)

        self.Layout()

    def set_data(self, data):
        self.clear_data()
        self.student_list.DeleteAllItems()
        self.student_list.DeleteAllColumns()
        # For ColumnSorterMixin data
        self.itemDataMap = {}
        row_num = 0
        try:
            for row in data:
                if self.headers is None:
                    # This is the first row, map columns
                    self.process_header_row(row)
                else:
                    row_num = self.process_data_row(row_num, row)
            if len(self.rows) > 0:
                self.button_print.Enable()
                self.button_generate.Enable()

            # Update ColumnSorterMixin column count
            self.SetColumnCount(len(self.headers))
            self.SortListItems(1)

            self.process_classes()

        except RuntimeError as e:
            self.clear_data()
            dlg = wx.MessageDialog(self, str(e), "Warning", wx.OK | wx.CANCEL)
            dlg.ShowModal()
            dlg.Destroy()

    def clear_data(self):
        self.headers = None
        self.rows = []
        self.classes = set()
        self.families = {}
        self.button_print.Disable()
        self.button_generate.Disable()

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
            self.student_list.InsertColumn(n, display_header)
            display_row.append(display_header)
        self.headers = display_row

    def process_data_row(self, row_num, row):
        display_row = []
        person = self.create_person(row)
        self.add_to_family(person)
        for class_name in person[CLASSES_COL]:
            self.classes.add(class_name)
        if display_filter(person):
            for c, column in enumerate(DISPLAY_COLUMNS):
                col_value = transform(column, person[column], DISPLAY_TRANSFORMS)
                if c == 0:
                    self.student_list.InsertItem(row_num, col_value)
                else:
                    self.student_list.SetItem(row_num, c, col_value)
                self.student_list.SetColumnWidth(c, wx.LIST_AUTOSIZE)
                display_row.append(col_value)
            self.rows.append(display_row)
            self.itemDataMap[row_num] = display_row
            self.student_list.SetItemData(row_num, row_num)
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
        self.fee_list.InsertColumn(0, 'Class')
        self.fee_list.InsertColumn(1, 'Teacher')
        self.fee_list.InsertColumn(2, 'Fee')
        for n, class_name in enumerate(sorted(self.classes)):
            self.fee_list.InsertItem(n, class_name)

    def on_print(self, event=None):
        prt = PrintTable(self.parent)
        prt.label = self.headers
        prt.data = self.rows
        prt.left_margin = .2
        prt.set_column = [2, 2, 2, 2]
        prt.top_margin = 1
        prt.SetLandscape()
        prt.SetHeader("Person List Report", size=30)
        prt.SetFooter("Page No", colour=wx.Colour('RED'), type="Num")
        prt.SetRowSpacing(10, 10)
        prt.Print()

    def on_generate(self, event=None):
        print('generating...')
        for family_id, family in self.families.items():
            self.create_invoice(family)

    def create_invoice(self, family):
        parents = get_parents(family)
        students = get_students(family)
        print('======================')
        for parent in parents:
            print('{:30}  {}'.format(
                parent[LAST_NAME_COL] + ', ' + parent[FIRST_NAME_COL], parent[EMAIL_COL]))
        for student in students:
            print('  {:28}'.format(student[LAST_NAME_COL] + ', ' + student[FIRST_NAME_COL]))
