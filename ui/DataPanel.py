import wx
from wx.lib.printout import PrintTable
import wx.lib.mixins.listctrl as listmix

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
    NONCONSECUTIVE_COL: 'Consecutive?',
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
    if bool_str is None or type(bool_str) != str:
        return False
    val = bool_str.strip().lower()
    return val not in ['', 'no', 'n', 'false', 'f', '0']


TRANSFORMS = {
    NONCONSECUTIVE_COL: lambda person: (person[MEMBER_TYPE_COL].strip().lower() == 'student'
                                        and not parse_bool(person[NONCONSECUTIVE_COL])),
    CLASSES_COL: lambda person: [t.strip() for t in person[CLASSES_COL].split(',')],
}


def transform(col_name, person):
    try:
        return TRANSFORMS[col_name](person)
    except KeyError:
        return person[col_name]


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


def filter_person(person):
    return person[MEMBER_TYPE_COL] == 'student'


class DataPanel(wx.Panel):
    """This Panel holds the main application data, a table of CSV values."""

    def __init__(self, parent, my_id, *args, **kwargs):
        """Create the main panel."""
        wx.Panel.__init__(self, parent, my_id, *args, **kwargs)

        self.headers = []
        self.rows = []
        self.column_name_to_idx = {}
        self.column_idx_to_name = {}
        self.families = {}
        self.parent = parent

        self.person_list = AutoWidthListCtrl(self, wx.ID_ANY,
                                             style=wx.LC_REPORT | wx.LC_SINGLE_SEL,
                                             size=(1, 150))

        self.button_print = wx.Button(self, wx.ID_ANY, "Print...")
        self.refresh()
        self.__do_layout()

    def __do_layout(self):

        box_outer = wx.BoxSizer(wx.VERTICAL)
        box_table = wx.BoxSizer(wx.VERTICAL)
        box_buttons = wx.BoxSizer(wx.HORIZONTAL)

        box_table.Add(self.person_list, 1, wx.EXPAND)

        box_buttons.Add(self.button_print, 0, wx.ALIGN_CENTER_HORIZONTAL | wx.ALIGN_CENTER_VERTICAL)

        box_outer.Add(box_table, 1, wx.EXPAND)
        box_outer.Add(box_buttons, 0, wx.EXPAND)
        self.SetAutoLayout(1)
        self.SetSizer(box_outer)
        box_outer.Fit(self)
        box_outer.SetSizeHints(self)

        self.Layout()

        self.Bind(wx.EVT_BUTTON, self.on_print, self.button_print)

    def set_data(self, data):
        self.clear_data()
        try:
            for row in data:
                if self.headers is None:
                    # This is the first row, map columns
                    self.process_header_row(row)
                else:
                    self.process_data_row(row)
        except RuntimeError as e:
            self.clear_data()
            dlg = wx.MessageDialog(self, str(e), "Warning", wx.OK | wx.CANCEL)
            dlg.ShowModal()
            dlg.Destroy()

    def clear_data(self):
        self.headers = None
        self.rows = []
        self.families = {}

    def process_header_row(self, row):
        self.column_name_to_idx = {}
        self.column_idx_to_name = {}
        display_row = []
        for n, header in enumerate(row):
            self.column_idx_to_name[n] = header
            self.column_name_to_idx[header] = n
        self.validate_header_row(row)
        for header in DISPLAY_COLUMNS:
            display_row.append(COLUMN_MAP[row[self.column_name_to_idx[header]]])
        self.headers = display_row

    def validate_header_row(self, row):
        missing_columns = []
        for column in DISPLAY_COLUMNS:
            if column not in row:
                missing_columns.append(column)
        if missing_columns:
            raise RuntimeError("Missing required columns: "
                               + ', '.join(missing_columns))

    def process_data_row(self, row):
        display_row = []
        person = self.create_person(row)
        self.add_to_family(person)
        if filter_person(person):
            for n, value in enumerate(row):
                col_name = self.column_idx_to_name[n]
                if col_name in DISPLAY_COLUMNS:
                    display_row.append(transform(col_name, person))
            self.rows.append(display_row)

    def add_to_family(self, person):
        family_id = person[FAMILY_ID_COL]
        try:
            self.families[family_id].append(person)
        except KeyError:
            self.families[family_id] = [person]

    def create_person(self, row):
        person = {}
        for n, column in enumerate(row):
            person[self.column_idx_to_name[n]] = column
        validate_person(person)
        return person

    def refresh(self):
        self.person_list.DeleteAllItems()
        self.person_list.DeleteAllColumns()

        for n, col in enumerate(self.headers):
            self.person_list.InsertColumn(n, col)

        for r, row in enumerate(self.rows):
            # print("row " + str(n) + ": " + str(row))
            for c, col in enumerate(row):
                if c == 0:
                    self.person_list.InsertItem(r, str(col))
                else:
                    self.person_list.SetItem(r, c, str(col))

        # self.person_list.SortItems()

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
