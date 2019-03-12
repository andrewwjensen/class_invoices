import csv
import os
import traceback
from decimal import Decimal

import wx
import wx.lib.mixins.listctrl as listmix

import mail
import pdf
import ui.EmailInfoWindow
from model.columns import Column
from model.family import get_parents, get_students
from model.parse import transform, REQUIRED_COLUMNS, validate_currency, parse_headers, parse_person
from ui.ListSorterPanel import ListSorterPanel
from util import start_thread

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


class AutoWidthListCtrl(wx.ListCtrl, listmix.ListCtrlAutoWidthMixin):
    def __init__(self, parent, wx_id, pos=wx.DefaultPosition, size=wx.DefaultSize, style=0):
        wx.ListCtrl.__init__(self, parent, wx_id, pos, size, style)
        listmix.ListCtrlAutoWidthMixin.__init__(self)


class AutoWidthEditableListCtrl(wx.ListCtrl, listmix.ListCtrlAutoWidthMixin,
                                listmix.TextEditMixin):
    def __init__(self, parent, wx_id, editable_columns=None, pos=wx.DefaultPosition, size=wx.DefaultSize, style=0):
        wx.ListCtrl.__init__(self, parent, wx_id, pos, size, style)
        listmix.ListCtrlAutoWidthMixin.__init__(self)
        listmix.TextEditMixin.__init__(self)
        self.editable_columns = editable_columns
        if editable_columns is None:
            self.editable_columns = []

    def OpenEditor(self, col, row):
        if col in self.editable_columns:
            listmix.TextEditMixin.OpenEditor(self, col, row)


def validate_fee_schedule_row(r, row):
    if len(row) < 3:
        raise RuntimeError('Too few columns in fee schedule on row {}: {}'.format(r + 1, row))
    if not row[1]:
        raise RuntimeError('Empty teacher in row {}, column 2 of fee schedule'.format(r + 1))
    if not validate_currency(row[2]):
        raise RuntimeError('Invalid currency in row {}, column 3 of fee schedule: {}'.format(r + 1, row[2]))
    return [row[0], row[1], validate_currency(row[2])]


class DataPanel(wx.Panel):
    """This Panel holds the main application data, a table of CSV values."""

    def clear_data(self):
        self.classes = set()
        self.families = {}
        self.student_panel.clear()
        self.fee_panel.clear()

        self.button_generate.Disable()
        self.button_email.Disable()
        self.button_import.Disable()
        self.button_export.Disable()

    def __init__(self, parent, my_id, *args, **kwargs):
        """Create the main panel."""
        wx.Panel.__init__(self, parent, my_id, *args, **kwargs)

        self.classes = set()
        self.families = {}
        self.parent = parent
        self.error_msg = None

        #######################################################################
        # Create splitter window and its two horizontal panels
        self.splitter = wx.SplitterWindow(self, wx.ID_ANY,
                                          style=wx.SP_3DBORDER | wx.SP_3D)
        self.student_panel = ListSorterPanel(self.splitter, wx.ID_ANY,
                                             AutoWidthListCtrl)
        self.fee_panel = ListSorterPanel(self.splitter, wx.ID_ANY,
                                         AutoWidthEditableListCtrl,
                                         editable_columns=[2])
        self.splitter.SplitVertically(self.student_panel, self.fee_panel)

        #######################################################################
        # Populate student panel (left)
        self.student_panel.SetMinSize((400, 100))

        # Create student panel buttons
        self.button_generate = wx.Button(self.student_panel, wx.ID_ANY,
                                         "Generate Invoices...")
        self.Bind(wx.EVT_BUTTON, self.on_generate, self.button_generate)
        self.button_generate.Disable()

        self.button_email = wx.Button(self.student_panel, wx.ID_ANY,
                                      "Email Invoices...")
        self.Bind(wx.EVT_BUTTON, self.on_email, self.button_email)
        self.button_email.Disable()

        student_buttons_sizer = wx.BoxSizer(wx.HORIZONTAL)
        student_buttons_sizer.Add(self.button_generate, 0,
                                  wx.ALIGN_CENTER_HORIZONTAL | wx.ALIGN_CENTER_VERTICAL, 5)
        student_buttons_sizer.Add(self.button_email, 0,
                                  wx.ALIGN_CENTER_HORIZONTAL | wx.ALIGN_CENTER_VERTICAL, 5)

        student_table_sizer = wx.BoxSizer(wx.VERTICAL)
        student_table_sizer.Add(self.student_panel.GetListCtrl(), 1, wx.EXPAND, 5)
        student_table_sizer.Add(student_buttons_sizer, 0, wx.EXPAND, 5)
        self.student_panel.SetSizer(student_table_sizer)

        #######################################################################
        # Populate fee schedule panel (right)
        self.fee_panel.SetMinSize((200, 100))

        # Create fee schedule panel buttons
        self.button_import = wx.Button(self.fee_panel, wx.ID_ANY,
                                       "Import Fee Schedule...")
        self.Bind(wx.EVT_BUTTON, self.on_import, self.button_import)
        self.button_import.Disable()

        self.button_export = wx.Button(self.fee_panel, wx.ID_ANY,
                                       "Export Fee Schedule to CSV...")
        self.Bind(wx.EVT_BUTTON, self.on_export, self.button_export)
        self.button_export.Disable()

        fee_buttons_sizer = wx.BoxSizer(wx.HORIZONTAL)
        fee_buttons_sizer.Add(self.button_import, 0,
                              wx.ALIGN_CENTER_HORIZONTAL | wx.ALIGN_CENTER_VERTICAL, 5)
        fee_buttons_sizer.Add(self.button_export, 0,
                              wx.ALIGN_CENTER_HORIZONTAL | wx.ALIGN_CENTER_VERTICAL, 5)

        fee_table_sizer = wx.BoxSizer(wx.VERTICAL)
        fee_table_sizer.Add(self.fee_panel.GetListCtrl(), 1, wx.EXPAND, 5)
        fee_table_sizer.Add(fee_buttons_sizer, 0, wx.EXPAND, 5)
        self.fee_panel.SetSizer(fee_table_sizer)

        #######################################################################
        # Add the splitter to a sizer and do the layout to pull everything together
        box_outer = wx.BoxSizer(wx.VERTICAL)
        box_outer.Add(self.splitter, 1, wx.EXPAND, 5)
        self.SetAutoLayout(True)
        self.SetSizer(box_outer)
        box_outer.SetSizeHints(self)
        self.Layout()
        # TODO: remove these
        # self.load_students(os.path.expandvars('${HOME}/Downloads/members-list.csv'))
        self.load_students(os.path.expandvars('${HOME}/Downloads/member-list-sm.csv'))
        # self.load_fee_schedule(os.path.expandvars('${HOME}/Downloads/Fee Schedule.csv'))

    def on_open(self, event=None):
        """Open a new CSV file."""
        dirname = ''
        file_dialog = wx.FileDialog(parent=self.parent,
                                    message="Choose a registration CSV file",
                                    defaultDir=dirname,
                                    defaultFile="",
                                    wildcard="*.csv",
                                    style=wx.FD_OPEN)
        if file_dialog.ShowModal() == wx.ID_OK:
            filename = file_dialog.GetFilename()
            dirname = file_dialog.GetDirectory()
            path = os.path.join(dirname, filename)
            try:
                self.load_students(path)
            except Exception as e:
                self.error_msg = "Error while opening registration file: " + str(e)
                traceback.print_exc()
        file_dialog.Destroy()
        self.check_error()

    def load_students(self, path):
        first_row = True
        families = {}
        column_idx_to_name = None
        with open(path, 'r') as f:
            reader = csv.reader(f)
            for row in reader:
                if first_row:
                    # This is the first row, process headers
                    column_idx_to_name = parse_headers(row)
                    first_row = False
                else:
                    parse_person(row, column_idx_to_name, families)
        self.clear_data()
        self.show_headers()
        self.show_families(families)

    def show_headers(self):
        display_row = []
        for n, header in enumerate(REQUIRED_COLUMNS):
            display_header = COLUMN_DISPLAY_MAP[header]
            self.student_panel.InsertColumn(n, display_header)
            display_row.append(display_header)
        # Update ColumnSorterMixin column count
        self.student_panel.SetColumnCount(len(REQUIRED_COLUMNS))

    def show_families(self, families):
        row_num = 0
        for family in families.values():
            row_num = self.show_students(row_num, get_students(family))
        self.families = families

        self.student_panel.SortListItems(1)

        self.show_classes()

        self.button_generate.Enable()
        self.button_email.Enable()
        self.button_import.Enable()
        self.button_export.Enable()

    def show_students(self, row_num, students):
        for student in students:
            for class_name in student[Column.CLASSES]:
                self.classes.add(class_name)
            for c, column in enumerate(REQUIRED_COLUMNS):
                col_value = transform(column, student[column], DISPLAY_TRANSFORMS)
                if c == 0:
                    self.student_panel.InsertItem(row_num, col_value)
                else:
                    self.student_panel.SetItem(row_num, c, col_value)
                self.student_panel.SetColumnWidth(c, wx.LIST_AUTOSIZE_USEHEADER)
            row_num += 1
        return row_num

    def show_classes(self):
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

    def on_export(self, event=None):
        dirname = ''
        file_dialog = wx.FileDialog(parent=self.parent,
                                    message="Export fee schedule to CSV",
                                    defaultDir=dirname,
                                    defaultFile="",
                                    wildcard="*.csv",
                                    style=wx.FD_SAVE)
        if file_dialog.ShowModal() == wx.ID_OK:
            filename = file_dialog.GetFilename()
            dirname = file_dialog.GetDirectory()
            try:
                with open(os.path.join(dirname, filename), 'w') as f:
                    csv_writer = csv.writer(f)
                    for r in range(self.fee_panel.GetListCtrl().GetItemCount()):
                        row = [self.fee_panel.GetListCtrl().GetItem(r, c).GetText() for
                               c in range(self.fee_panel.GetListCtrl().GetColumnCount())]
                        csv_writer.writerow(row)
            except Exception as e:
                self.error_msg = "Error while exporting fee schedule: " + str(e)
                traceback.print_exc()
        file_dialog.Destroy()
        self.check_error()

    def on_import(self, event=None):
        dirname = ''
        file_dialog = wx.FileDialog(parent=self.parent,
                                    message="Choose a fee schedule CSV file",
                                    defaultDir=dirname,
                                    defaultFile="",
                                    wildcard="*.csv",
                                    style=wx.FD_OPEN)
        if file_dialog.ShowModal() == wx.ID_OK:
            filename = file_dialog.GetFilename()
            dirname = file_dialog.GetDirectory()
            try:
                self.load_fee_schedule(os.path.join(dirname, filename))
            except Exception as e:
                self.error_msg = "Error while reading fee schedule: " + str(e)
                traceback.print_exc()
        file_dialog.Destroy()
        self.check_error()

    def on_generate(self, event=None):
        progress = wx.ProgressDialog("Generating Invoices",
                                     "Please wait...\n\n"
                                     "Generating invoice for family:",
                                     maximum=len(self.families), parent=self,
                                     style=wx.PD_SMOOTH | wx.PD_APP_MODAL | wx.PD_ELAPSED_TIME | wx.PD_CAN_ABORT
                                     )
        start_thread(self.generate_invoices, progress)
        progress.ShowModal()
        self.check_error()

    def on_email(self, event=None):
        # message = self.get_subject()
        # message = self.get_message()
        frame = ui.EmailInfoWindow(self, wx.ID_ANY, 'Email Info')
        frame.ShowModal()
        return
        progress = wx.ProgressDialog("Emailing Invoices",
                                     "Please wait...\n\n"
                                     "Emailing invoice for family:",
                                     maximum=len(self.families), parent=self,
                                     style=wx.PD_SMOOTH | wx.PD_APP_MODAL | wx.PD_ELAPSED_TIME | wx.PD_CAN_ABORT
                                     )
        start_thread(self.email_invoices, message, progress)
        progress.ShowModal()
        self.check_error()

    def generate_invoices(self, progress):
        n = 1
        try:
            class_map = self.validate_fee_schedule()
            for family_id, family in self.families.items():
                if progress.WasCancelled():
                    break
                msg = "Please wait...\n\n" \
                      "Generating invoice for family: {fam}".format(fam=family['last_name'])
                wx.CallAfter(progress.Update, n - 1, newmsg=msg)
                if get_students(family):
                    with open('invoice{:03}.pdf'.format(n), 'wb') as f:
                        f.write(self.create_invoice(family, class_map))
                        n += 1
        except Exception as e:
            self.error_msg = "Error while generating invoices: " + str(e)
            traceback.print_exc()
        wx.CallAfter(progress.EndModal, 0)
        wx.CallAfter(progress.Destroy)

    def email_invoices(self, message, progress):
        try:
            class_map = self.validate_fee_schedule()
            gmail_service = mail.get_gmail_service()
            profile = gmail_service.users().getProfile(userId='me').execute()
            sender = profile['emailAddress']
            n = 1
            for family_id, family in self.families.items():
                if progress.WasCancelled():
                    break
                msg = "Please wait...\n\n" \
                      "Emailing invoice for family: {fam}".format(fam=family['last_name'])
                wx.CallAfter(progress.Update, n - 1, newmsg=msg)
                if get_students(family):
                    pdf_attachment = self.create_invoice(family, class_map)
                    n += 1
                    recipients = [p[Column.EMAIL] for p in family['parents']]
                    if recipients:
                        msg = mail.create_message_with_attachment(sender=sender, recipients=recipients,
                                                                  subject='Class Enrollment Invoice',
                                                                  message_text=message, data=pdf_attachment)
                        print('msg:', msg)
                        mail.create_draft(gmail_service, 'me', msg)
        except Exception as e:
            self.error_msg = "Error while sending email: " + str(e)
            traceback.print_exc()
        print('here')
        wx.CallAfter(progress.EndModal, 0)
        wx.CallAfter(progress.Destroy)

    def load_fee_schedule(self, path):
        # First, build a map of class name to row number on the displayed fee schedule
        class_to_row = {}
        for r in range(self.fee_panel.GetListCtrl().GetItemCount()):
            class_name = self.fee_panel.GetListCtrl().GetItem(r, 0).GetText()
            class_to_row[class_name] = r

        # Now open the fee schedule CSV and process its rows
        with open(path, 'r') as f:
            reader = csv.reader(f)
            r = 0
            for row in reader:
                try:
                    row = validate_fee_schedule_row(r, row)
                    display_row_num = class_to_row[row[0]]
                    self.fee_panel.SetItem(display_row_num, 1, row[1])
                    self.fee_panel.SetItem(display_row_num, 2, row[2])
                except KeyError:
                    # Ignore classes that are not needed for any registered student
                    pass
                except RuntimeError:
                    # Ignore validation error on first row, as it may be a header row
                    if r != 0:
                        raise
                r += 1
        self.fee_panel.SetColumnWidth(1, wx.LIST_AUTOSIZE_USEHEADER)
        self.fee_panel.SetColumnWidth(2, wx.LIST_AUTOSIZE_USEHEADER)
        self.fee_panel.Refresh()

    def validate_fee_schedule(self):
        class_map = {}
        missing_classes = []
        for r in range(self.fee_panel.GetListCtrl().GetItemCount()):
            class_name = self.fee_panel.GetListCtrl().GetItem(r, 0).GetText()
            teacher = self.fee_panel.GetListCtrl().GetItem(r, 1).GetText()
            fee = self.fee_panel.GetListCtrl().GetItem(r, 2).GetText()
            if not teacher or not fee:
                missing_classes.append(class_name)
            else:
                class_map[class_name] = (teacher, Decimal(fee))
        if missing_classes:
            msg = 'Classes have missing teacher or fee:\n  ' + '\n  '.join(missing_classes)
            raise RuntimeError(msg)
        return class_map

    def create_invoice(self, family, class_map):
        invoice = {}
        parents = get_parents(family)
        students = get_students(family)
        invoice['parent'] = []
        for parent in parents:
            invoice['parent'].append([
                parent[Column.LAST_NAME] + ', ' + parent[Column.FIRST_NAME],
                parent[Column.EMAIL]])
        payable = {}
        invoice['students'] = {}
        invoice['total'] = Decimal(0.00)
        for student in students:
            name = student[Column.LAST_NAME] + ', ' + student[Column.FIRST_NAME]
            invoice['students'][name] = []
            for class_name in student[Column.CLASSES]:
                teacher, fee = class_map[class_name]
                invoice['students'][name].append([class_name, teacher, fee])
                invoice['total'] += fee
                try:
                    payable[teacher] += fee
                except KeyError:
                    payable[teacher] = fee
        invoice['payable'] = payable
        return pdf.generate(invoice, 'invoice.pdf')

    def check_error(self):
        if self.error_msg:
            caption = 'Error'
            dlg = wx.MessageDialog(self, self.error_msg,
                                   caption, wx.OK | wx.ICON_WARNING)
            self.error_msg = None
            dlg.ShowModal()
            dlg.Destroy()
