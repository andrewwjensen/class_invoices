import traceback
from decimal import Decimal

import wx
import wx.lib.newevent

from mail.gmail import send_emails
from model.columns import Column
from util import start_thread

DEFAULT_BORDER = 5


class EmailPanel(wx.Panel):

    def __init__(self, enrollment_panel, border=DEFAULT_BORDER, *args, **kwargs):
        wx.Panel.__init__(self, *args, **kwargs)

        self.button_email_invoices = wx.Button(self, wx.ID_ANY, "Email Invoices...")
        self.text_ctrl_email_subject = wx.TextCtrl(self, wx.ID_ANY, "")
        self.text_ctrl_email_body = wx.TextCtrl(self, wx.ID_ANY, "", style=wx.TE_MULTILINE)

        self.enrollment_panel = enrollment_panel
        self.modified = False
        self.error_msg = None

        self.__do_layout(border)

    def __do_layout(self, border):
        sizer_email_tab = wx.BoxSizer(wx.VERTICAL)
        sizer_email_tab_subject_row = wx.BoxSizer(wx.HORIZONTAL)
        sizer_email_tab_body_row = wx.BoxSizer(wx.HORIZONTAL)
        sizer_email_tab_button_row = wx.BoxSizer(wx.HORIZONTAL)

        label_subject = wx.StaticText(self, wx.ID_ANY, "Subject")
        sizer_email_tab_subject_row.Add(label_subject, 0, wx.ALL, border)
        sizer_email_tab_subject_row.Add(self.text_ctrl_email_subject, 1, wx.EXPAND | wx.ALL, border)
        sizer_email_tab.Add(sizer_email_tab_subject_row, 0, wx.ALL, border)

        label_body = wx.StaticText(self, wx.ID_ANY, "Body")
        sizer_email_tab_body_row.Add(label_body, 0, wx.ALL, border)
        sizer_email_tab_body_row.Add(self.text_ctrl_email_body, 1, wx.EXPAND | wx.ALL, border)
        sizer_email_tab.Add(sizer_email_tab_body_row, 1, wx.EXPAND | wx.ALL, border)

        sizer_email_tab_button_row.Add(self.button_email_invoices, 0, wx.ALL, border)
        self.Bind(wx.EVT_BUTTON, self.on_email, self.button_email_invoices)
        sizer_email_tab.Add(sizer_email_tab_button_row, 0, wx.ALIGN_RIGHT | wx.ALL, border)
        self.SetSizer(sizer_email_tab)

        self.button_email_invoices.Disable()

    def get_name(self):
        return 'Email'

    def is_modified(self):
        return self.modified or self.text_ctrl_email_body.IsModified() or self.text_ctrl_email_subject.IsModified()

    def set_is_modified(self, modified=True):
        self.modified = modified
        self.text_ctrl_email_body.SetModified(modified)
        self.text_ctrl_email_subject.SetModified(modified)

    def enable_buttons(self, enable=True):
        self.button_email_invoices.Enable(enable)

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
                    progress = wx.ProgressDialog(
                        parent=self,
                        title="Emailing Invoices",
                        message="Please wait...\n\n"
                                "Emailing invoice for family:",
                        maximum=len(self.enrollment_panel.get_families()),
                        style=wx.PD_SMOOTH | wx.PD_APP_MODAL | wx.PD_ELAPSED_TIME | wx.PD_CAN_ABORT)
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
            send_emails(subject, body,
                        self.enrollment_panel.get_families(),
                        self.enrollment_panel.get_class_map(),
                        progress)
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
        for family in self.enrollment_panel.get_families().values():
            for student in family['students']:
                for class_name in student[Column.CLASSES]:
                    try:
                        teacher, fee = self.enrollment_panel.get_class_map()[class_name]
                        if not teacher or not fee or not type(fee) == Decimal:
                            missing_fees.append(class_name)
                    except KeyError:
                        missing_fees.append(class_name)
        if missing_fees:
            raise RuntimeError('missing teacher or fee for classes:\n    ' + '\n    '.join(missing_fees))

    def get_data(self):
        return {
            'subject': self.text_ctrl_email_subject.GetValue(),
            'body': self.text_ctrl_email_body.GetValue(),
        }

    def load_data(self, data):
        self.text_ctrl_email_subject.SetValue(data['subject'])
        self.text_ctrl_email_body.SetValue(data['body'])
