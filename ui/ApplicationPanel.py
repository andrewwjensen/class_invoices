import os
import traceback
from decimal import Decimal

import wx

from mail.gmail import send_emails
from model.columns import Column
from model.family import get_classes, load_families
from pdf.generate import generate_invoices
from ui.FeeSchedulePanel import FeeSchedulePanel
from util import start_thread

BORDER_WIDTH = 5

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


class ApplicationPanel(wx.Panel):
    """This Panel holds the main application data, a table of CSV values."""

    def clear_data(self):
        self.families = {}

    def __init__(self, parent, *args, **kwargs):
        # begin wxGlade: MyFrame.__init__
        wx.Panel.__init__(self, parent, *args, **kwargs)

        self.SetSize((842, 554))

        self.splitter = wx.SplitterWindow(self, wx.ID_ANY)
        self.enrollment_split = wx.Panel(self.splitter, wx.ID_ANY)
        self.button_load_enrollment = wx.Button(self.enrollment_split, wx.ID_ANY, "Load Enrollment List...")
        self.button_show_students = wx.Button(self.enrollment_split, wx.ID_ANY, "Show Student List...")

        self.action_tabs = wx.Notebook(self.enrollment_split, wx.ID_ANY)

        self.pdf_tab = wx.Panel(self.action_tabs, wx.ID_ANY)
        self.button_generate_master = wx.Button(self.pdf_tab, wx.ID_ANY, "Generate Master PDF...")
        self.button_generate_invoices = wx.Button(self.pdf_tab, wx.ID_ANY, "Generate Invoices...")

        self.email_tab = wx.Panel(self.action_tabs, wx.ID_ANY)
        self.text_ctrl_email_subject = wx.TextCtrl(self.email_tab, wx.ID_ANY, "")
        self.text_ctrl_email_body = wx.TextCtrl(self.email_tab, wx.ID_ANY, "", style=wx.TE_MULTILINE)
        self.button_email_invoices = wx.Button(self.email_tab, wx.ID_ANY, "Email Invoices...")

        self.fee_schedule_split = FeeSchedulePanel(parent=self.splitter, border=BORDER_WIDTH)

        self.__set_properties()
        self.__do_layout()
        # end wxGlade

        self.Bind(wx.EVT_SIZE, self.on_resize)

        self.families = {}
        self.error_msg = None

        # TODO: remove these
        # self.load_students(os.path.expandvars('${HOME}/Downloads/members-list.csv'))
        self.load_enrollment_data(os.path.expandvars('${HOME}/Downloads/member-list-sm.csv'))
        # self.load_fee_schedule(os.path.expandvars('${HOME}/Downloads/Fee Schedule.csv'))

    def __set_properties(self):
        # begin wxGlade: MyFrame.__set_properties
        self.splitter.SetMinimumPaneSize(350)
        # end wxGlade

    def __do_layout(self):
        # begin wxGlade: MyFrame.__do_layout
        sizer_window = wx.BoxSizer(wx.VERTICAL)
        sizer_enrollment_split = wx.BoxSizer(wx.VERTICAL)
        sizer_email_tab = wx.BoxSizer(wx.VERTICAL)
        sizer_email_tab_subject_row = wx.BoxSizer(wx.HORIZONTAL)
        sizer_email_tab_body_row = wx.BoxSizer(wx.HORIZONTAL)
        sizer_email_tab_button_row = wx.BoxSizer(wx.HORIZONTAL)
        sizer_pdf_tab = wx.BoxSizer(wx.VERTICAL)
        sizer_enrollment_pane = wx.BoxSizer(wx.VERTICAL)
        sizer_stats = wx.BoxSizer(wx.HORIZONTAL)

        # Enrollment pane (left half of splitter)
        sizer_enrollment_pane.Add(self.button_load_enrollment, 0, wx.ALL, BORDER_WIDTH)
        self.Bind(wx.EVT_BUTTON, self.on_load, self.button_load_enrollment)
        label_families = wx.StaticText(self.enrollment_split, wx.ID_ANY, "Families:")
        sizer_stats.Add(label_families, 0, wx.LEFT | wx.TOP | wx.BOTTOM, BORDER_WIDTH)
        self.label_num_families = wx.StaticText(self.enrollment_split, wx.ID_ANY, "0")
        sizer_stats.Add(self.label_num_families, 0, wx.RIGHT | wx.TOP | wx.BOTTOM, BORDER_WIDTH)
        label_parents = wx.StaticText(self.enrollment_split, wx.ID_ANY, "Parents:")
        sizer_stats.Add(label_parents, 0, wx.LEFT | wx.TOP | wx.BOTTOM, BORDER_WIDTH)
        self.label_num_parents = wx.StaticText(self.enrollment_split, wx.ID_ANY, "0")
        sizer_stats.Add(self.label_num_parents, 0, wx.RIGHT | wx.TOP | wx.BOTTOM, BORDER_WIDTH)
        label_students = wx.StaticText(self.enrollment_split, wx.ID_ANY, "Students:")
        sizer_stats.Add(label_students, 0, wx.LEFT | wx.TOP | wx.BOTTOM, BORDER_WIDTH)
        self.label_num_students = wx.StaticText(self.enrollment_split, wx.ID_ANY, "0")
        sizer_stats.Add(self.label_num_students, 0, wx.RIGHT | wx.TOP | wx.BOTTOM, BORDER_WIDTH)
        sizer_enrollment_pane.Add(sizer_stats, 1, wx.EXPAND, BORDER_WIDTH)
        sizer_enrollment_pane.Add(self.button_show_students, 0, wx.ALL, BORDER_WIDTH)
        self.Bind(wx.EVT_BUTTON, self.show_students, self.button_show_students)
        sizer_enrollment_split.Add(sizer_enrollment_pane, 0, wx.EXPAND | wx.ALL, BORDER_WIDTH)

        # PDF tab of the action notebook
        sizer_pdf_tab.Add(self.button_generate_master, 0, wx.ALL, BORDER_WIDTH)
        self.Bind(wx.EVT_BUTTON, self.on_generate_master, self.button_generate_master)
        sizer_pdf_tab.Add(self.button_generate_invoices, 0, wx.ALL, BORDER_WIDTH)
        self.Bind(wx.EVT_BUTTON, self.on_generate_invoices, self.button_generate_invoices)
        self.pdf_tab.SetSizer(sizer_pdf_tab)

        # Email tab of the action notebook
        label_subject = wx.StaticText(self.email_tab, wx.ID_ANY, "Subject")
        sizer_email_tab_subject_row.Add(label_subject, 0, wx.ALL, BORDER_WIDTH)
        sizer_email_tab_subject_row.Add(self.text_ctrl_email_subject, 1, wx.EXPAND | wx.ALL, BORDER_WIDTH)
        sizer_email_tab.Add(sizer_email_tab_subject_row, 0, wx.ALL, BORDER_WIDTH)

        label_body = wx.StaticText(self.email_tab, wx.ID_ANY, "Body")
        sizer_email_tab_body_row.Add(label_body, 0, wx.ALL, BORDER_WIDTH)
        sizer_email_tab_body_row.Add(self.text_ctrl_email_body, 1, wx.EXPAND | wx.ALL, BORDER_WIDTH)
        sizer_email_tab.Add(sizer_email_tab_body_row, 1, wx.EXPAND | wx.ALL, BORDER_WIDTH)

        sizer_email_tab_button_row.Add(self.button_email_invoices, 0, wx.ALL, BORDER_WIDTH)
        self.Bind(wx.EVT_BUTTON, self.on_email, self.button_email_invoices)
        sizer_email_tab.Add(sizer_email_tab_button_row, 0, wx.ALIGN_RIGHT | wx.ALL, BORDER_WIDTH)
        self.email_tab.SetSizer(sizer_email_tab)

        # Disable all buttons except Load
        self.button_show_students.Disable()
        self.button_generate_master.Disable()
        self.button_generate_invoices.Disable()
        self.button_email_invoices.Disable()

        # Pull it all together into the main sizer
        self.action_tabs.AddPage(self.pdf_tab, "PDF")
        self.action_tabs.AddPage(self.email_tab, "Email")
        sizer_enrollment_split.Add(self.action_tabs, 1, wx.EXPAND | wx.ALL, BORDER_WIDTH)
        self.enrollment_split.SetSizer(sizer_enrollment_split)
        self.splitter.SplitVertically(self.enrollment_split, self.fee_schedule_split)
        sizer_window.Add(self.splitter, 1, wx.EXPAND | wx.ALL, BORDER_WIDTH)
        self.SetSizer(sizer_window)
        self.SetAutoLayout(True)
        self.Layout()
        # end wxGlade

    def on_resize(self, event):
        """Window has been resized, so we need to adjust the sash based on self.proportion."""
        self.splitter.SetSashPosition(self.get_expected_sash_position())
        self.splitter.SetSashSize(0)
        event.Skip()
        print(self.GetSize())

    def get_expected_sash_position(self):
        proportion = self.splitter.GetSize()
        width = max(self.splitter.GetMinimumPaneSize(), self.GetParent().GetClientSize().width)
        return int(round(width / 2.0))

    def on_load(self, event=None):
        """Load a new class enrollment CSV file."""
        dirname = ''
        file_dialog = wx.FileDialog(parent=self,
                                    message="Choose an enrollment CSV file",
                                    defaultDir=dirname,
                                    defaultFile="",
                                    wildcard="*.csv",
                                    style=wx.FD_OPEN)
        if file_dialog.ShowModal() == wx.ID_OK:
            filename = file_dialog.GetFilename()
            dirname = file_dialog.GetDirectory()
            path = os.path.join(dirname, filename)
            try:
                self.load_enrollment_data(path)
            except Exception as e:
                self.error_msg = "Error while opening enrollment file: " + str(e)
                traceback.print_exc()
        file_dialog.Destroy()
        self.check_error()

    def load_enrollment_data(self, path):
        self.families = load_families(path)
        self.set_stats()
        self.populate_fee_schedule()
        self.enable_buttons()

    def set_stats(self):
        num_families = len(self.families)
        num_parents = 0
        num_students = 0
        for family in self.families.values():
            num_parents += len(family['parents'])
            num_students += len(family['students'])
        self.label_num_families.SetLabelText(str(num_families))
        self.label_num_parents.SetLabelText(str(num_parents))
        self.label_num_students.SetLabelText(str(num_students))
        # Force the panel to redo its layout since widths may have changed:
        self.enrollment_split.Layout()

    def populate_fee_schedule(self):
        self.fee_schedule_split.add_column('Class')
        self.fee_schedule_split.add_column('Teacher')
        self.fee_schedule_split.add_column('Fee')

        for class_name in get_classes(self.families):
            self.fee_schedule_split.add_row([class_name, '', ''], dedup_col=0)

        self.fee_schedule_split.resize_column(0)
        self.fee_schedule_split.SortListItems(0)

    def enable_buttons(self):
        self.button_show_students.Enable()
        self.button_generate_master.Enable()
        self.button_generate_invoices.Enable()
        self.button_email_invoices.Enable()
        self.fee_schedule_split.enable_buttons()

    def show_students(self):
        pass

    def on_generate_master(self, event=None):
        progress = wx.ProgressDialog("Generating Master PDF",
                                     "Please wait...\n\n"
                                     "Processing family:",
                                     maximum=len(self.families), parent=self,
                                     style=wx.PD_SMOOTH | wx.PD_APP_MODAL | wx.PD_ELAPSED_TIME | wx.PD_CAN_ABORT
                                     )
        # start_thread(self.generate_invoices, progress)
        progress.ShowModal()
        self.check_error()

    def on_generate_invoices(self, event=None):
        progress = wx.ProgressDialog("Generating Invoices",
                                     "Please wait...\n\n"
                                     "Generating invoice for family:",
                                     maximum=len(self.families), parent=self,
                                     style=wx.PD_SMOOTH | wx.PD_APP_MODAL | wx.PD_ELAPSED_TIME | wx.PD_CAN_ABORT
                                     )
        start_thread(generate_invoices, progress)
        progress.ShowModal()
        self.check_error()

    def on_email(self, event=None):
        subject = self.text_ctrl_email_subject.GetValue()
        message = self.text_ctrl_email_body.GetValue()
        progress = wx.ProgressDialog("Emailing Invoices",
                                     "Please wait...\n\n"
                                     "Emailing invoice for family:",
                                     maximum=len(self.families), parent=self,
                                     style=wx.PD_SMOOTH | wx.PD_APP_MODAL | wx.PD_ELAPSED_TIME | wx.PD_CAN_ABORT
                                     )
        start_thread(self.email_invoices, subject, message, progress)
        progress.ShowModal()
        self.check_error()

    def email_invoices(self, subject, message, progress):
        try:
            class_map = self.validate_fee_schedule()
            send_emails(subject, message, self.families, class_map, progress)
        except Exception as e:
            self.error_msg = "Error while sending email: " + str(e)
            traceback.print_exc()
        print('here')
        wx.CallAfter(progress.EndModal, 0)
        wx.CallAfter(progress.Destroy)

    def validate_fee_schedule(self):
        class_map = {}
        missing_classes = []
        for r in range(self.fee_schedule_split.GetListCtrl().GetItemCount()):
            class_name = self.fee_schedule_split.GetListCtrl().GetItem(r, 0).GetText()
            teacher = self.fee_schedule_split.GetListCtrl().GetItem(r, 1).GetText()
            fee = self.fee_schedule_split.GetListCtrl().GetItem(r, 2).GetText()
            if not teacher or not fee:
                missing_classes.append(class_name)
            else:
                class_map[class_name] = (teacher, Decimal(fee))
        if missing_classes:
            msg = 'Classes have missing teacher or fee:\n  ' + '\n  '.join(missing_classes)
            raise RuntimeError(msg)
        return class_map

    def check_error(self):
        if self.error_msg:
            caption = 'Error'
            dlg = wx.MessageDialog(self, self.error_msg,
                                   caption, wx.OK | wx.ICON_WARNING)
            self.error_msg = None
            dlg.ShowModal()
            dlg.Destroy()
