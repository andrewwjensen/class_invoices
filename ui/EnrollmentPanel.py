import os
import traceback
from decimal import Decimal

import wx
import wx.lib.newevent

from mail.gmail import send_emails
from model.columns import Column
from model.family import load_families
from pdf.generate import generate_invoices
from util import start_thread

DEFAULT_BORDER = 5


class EnrollmentPanel(wx.Panel):
    EnrollmentDataEvent, EVT_ENROLLMENT_DATA_CHANGED = wx.lib.newevent.NewEvent()

    def __init__(self, border=DEFAULT_BORDER, *args, **kwargs):
        wx.Panel.__init__(self, *args, **kwargs)
        self.button_load_enrollment = wx.Button(self, wx.ID_ANY, "Load Enrollment List...")
        self.button_show_students = wx.Button(self, wx.ID_ANY, "Show Student List...")

        self.action_tabs = wx.Notebook(self, wx.ID_ANY)

        self.pdf_tab = wx.Panel(self.action_tabs, wx.ID_ANY)
        self.button_generate_master = wx.Button(self.pdf_tab, wx.ID_ANY, "Generate Master PDF...")
        self.button_generate_invoices = wx.Button(self.pdf_tab, wx.ID_ANY, "Generate Invoices...")

        self.email_tab = wx.Panel(self.action_tabs, wx.ID_ANY)
        self.text_ctrl_email_subject = wx.TextCtrl(self.email_tab, wx.ID_ANY, "")
        self.text_ctrl_email_body = wx.TextCtrl(self.email_tab, wx.ID_ANY, "", style=wx.TE_MULTILINE)
        self.button_email_invoices = wx.Button(self.email_tab, wx.ID_ANY, "Email Invoices...")
        self.__do_layout(border)

        self.families = {}
        self.class_map = {}
        self.modified = False
        self.error_msg = None

    def __do_layout(self, border):
        sizer_enrollment_split = wx.BoxSizer(wx.VERTICAL)
        sizer_email_tab = wx.BoxSizer(wx.VERTICAL)
        sizer_email_tab_subject_row = wx.BoxSizer(wx.HORIZONTAL)
        sizer_email_tab_body_row = wx.BoxSizer(wx.HORIZONTAL)
        sizer_email_tab_button_row = wx.BoxSizer(wx.HORIZONTAL)
        sizer_pdf_tab = wx.BoxSizer(wx.VERTICAL)
        sizer_enrollment_pane = wx.BoxSizer(wx.VERTICAL)
        sizer_stats = wx.BoxSizer(wx.HORIZONTAL)

        # Enrollment pane (left half of splitter)
        sizer_enrollment_pane.Add(self.button_load_enrollment, 0, wx.ALL, border)
        self.Bind(wx.EVT_BUTTON, self.on_load, self.button_load_enrollment)
        label_families = wx.StaticText(self, wx.ID_ANY, "Families:")
        sizer_stats.Add(label_families, 0, wx.LEFT | wx.TOP | wx.BOTTOM, border)
        self.label_num_families = wx.StaticText(self, wx.ID_ANY, "0")
        sizer_stats.Add(self.label_num_families, 0, wx.RIGHT | wx.TOP | wx.BOTTOM, border)
        label_parents = wx.StaticText(self, wx.ID_ANY, "Parents:")
        sizer_stats.Add(label_parents, 0, wx.LEFT | wx.TOP | wx.BOTTOM, border)
        self.label_num_parents = wx.StaticText(self, wx.ID_ANY, "0")
        sizer_stats.Add(self.label_num_parents, 0, wx.RIGHT | wx.TOP | wx.BOTTOM, border)
        label_students = wx.StaticText(self, wx.ID_ANY, "Students:")
        sizer_stats.Add(label_students, 0, wx.LEFT | wx.TOP | wx.BOTTOM, border)
        self.label_num_students = wx.StaticText(self, wx.ID_ANY, "0")
        sizer_stats.Add(self.label_num_students, 0, wx.RIGHT | wx.TOP | wx.BOTTOM, border)
        sizer_enrollment_pane.Add(sizer_stats, 1, wx.EXPAND, border)
        sizer_enrollment_pane.Add(self.button_show_students, 0, wx.ALL, border)
        self.Bind(wx.EVT_BUTTON, self.show_students, self.button_show_students)
        sizer_enrollment_split.Add(sizer_enrollment_pane, 0, wx.EXPAND | wx.ALL, border)

        # PDF tab of the action notebook
        sizer_pdf_tab.Add(self.button_generate_master, 0, wx.ALL, border)
        self.Bind(wx.EVT_BUTTON, self.on_generate_master, self.button_generate_master)
        sizer_pdf_tab.Add(self.button_generate_invoices, 0, wx.ALL, border)
        self.Bind(wx.EVT_BUTTON, self.on_generate_invoices, self.button_generate_invoices)
        self.pdf_tab.SetSizer(sizer_pdf_tab)

        # Email tab of the action notebook
        label_subject = wx.StaticText(self.email_tab, wx.ID_ANY, "Subject")
        sizer_email_tab_subject_row.Add(label_subject, 0, wx.ALL, border)
        sizer_email_tab_subject_row.Add(self.text_ctrl_email_subject, 1, wx.EXPAND | wx.ALL, border)
        sizer_email_tab.Add(sizer_email_tab_subject_row, 0, wx.ALL, border)

        label_body = wx.StaticText(self.email_tab, wx.ID_ANY, "Body")
        sizer_email_tab_body_row.Add(label_body, 0, wx.ALL, border)
        sizer_email_tab_body_row.Add(self.text_ctrl_email_body, 1, wx.EXPAND | wx.ALL, border)
        sizer_email_tab.Add(sizer_email_tab_body_row, 1, wx.EXPAND | wx.ALL, border)

        sizer_email_tab_button_row.Add(self.button_email_invoices, 0, wx.ALL, border)
        self.Bind(wx.EVT_BUTTON, self.on_email, self.button_email_invoices)
        sizer_email_tab.Add(sizer_email_tab_button_row, 0, wx.ALIGN_RIGHT | wx.ALL, border)
        self.email_tab.SetSizer(sizer_email_tab)

        # Disable all buttons except Load
        self.button_show_students.Disable()
        self.button_generate_master.Disable()
        self.button_generate_invoices.Disable()
        self.button_email_invoices.Disable()

        # Pull it all together into the main sizer
        self.action_tabs.AddPage(self.pdf_tab, "PDF")
        self.action_tabs.AddPage(self.email_tab, "Email")
        sizer_enrollment_split.Add(self.action_tabs, 1, wx.EXPAND | wx.ALL, border)
        self.SetSizer(sizer_enrollment_split)

    def is_modified(self):
        return self.modified

    def get_families(self):
        return self.families

    def set_class_map(self, class_map):
        self.class_map = class_map
        print('got class map:', class_map)

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
                self.modified = True
            except Exception as e:
                self.error_msg = "Error while opening enrollment file: " + str(e)
                traceback.print_exc()
        file_dialog.Destroy()
        self.check_error()

    def load_enrollment_data(self, path):
        self.families = load_families(path)
        self.set_stats()
        self.enable_buttons()
        event = self.EnrollmentDataEvent()
        wx.PostEvent(self.GetEventHandler(), event)

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
        self.Layout()

    def enable_buttons(self, enable=True):
        self.button_show_students.Enable()
        self.button_generate_master.Enable()
        self.button_generate_invoices.Enable()
        self.button_email_invoices.Enable()

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
        body = self.text_ctrl_email_body.GetValue()
        try:
            if not subject.strip():
                self.error_msg = 'Email subject may not be empty.'
                self.text_ctrl_email_subject.SetFocus()
            else:
                if not body.strip():
                    self.error_msg = 'Enter a message body before sending email.'
                    self.text_ctrl_email_body.SetFocus()
                else:
                    progress = wx.ProgressDialog("Emailing Invoices",
                                                 "Please wait...\n\n"
                                                 "Emailing invoice for family:",
                                                 maximum=len(self.families), parent=self,
                                                 style=wx.PD_SMOOTH | wx.PD_APP_MODAL | wx.PD_ELAPSED_TIME | wx.PD_CAN_ABORT
                                                 )
                    start_thread(self.email_invoices, subject, body, progress)
                    progress.ShowModal()
        except Exception as e:
            self.error_msg = "Error while sending email: " + str(e)
            traceback.print_exc()
        self.check_error()
        if not subject.strip():
            self.text_ctrl_email_subject.SetFocus()
        elif not body.strip():
            self.text_ctrl_email_body.SetFocus()

    def email_invoices(self, subject, body, progress):
        try:
            self.validate_fee_schedule()
            send_emails(subject, body, self.families, self.class_map, progress)
        except KeyError as e:
            self.error_msg = "Missing teacher or fee for class while sending email: " + e.args[0]
            traceback.print_exc()
        except Exception as e:
            self.error_msg = "Error while sending email: " + str(e)
            traceback.print_exc()
        wx.CallAfter(progress.EndModal, 0)
        wx.CallAfter(progress.Destroy)

    def check_error(self):
        if self.error_msg:
            caption = 'Error'
            dlg = wx.MessageDialog(self, self.error_msg,
                                   caption, wx.OK | wx.ICON_WARNING)
            self.error_msg = None
            dlg.ShowModal()
            dlg.Destroy()

    def validate_fee_schedule(self):
        missing_fees = []
        for family in self.families.values():
            for student in family['students']:
                for class_name in student[Column.CLASSES]:
                    try:
                        teacher, fee = self.class_map[class_name]
                        if not teacher or not fee or not type(fee) == Decimal:
                            missing_fees.append(class_name)
                    except KeyError:
                        missing_fees.append(class_name)
        if missing_fees:
            raise RuntimeError('missing teacher or fee for classes:\n    ' + '\n    '.join(missing_fees))
