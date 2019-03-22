import logging
import tempfile

import wx
import wx.lib.newevent

import app_config
from mail import gmail
from mail.gmail import check_credentials
from model.columns import Column
from pdf.generate import generate_invoices
from ui.PDFViewer import PDFViewer
from util import start_thread, MyBytesIO

DEFAULT_BORDER = 5

logging.basicConfig()
logger = logging.getLogger(app_config.APP_NAME)
logger.setLevel(logging.INFO)


class PdfPanel(wx.Panel):

    def __init__(self, border=DEFAULT_BORDER, *args, **kwargs):
        wx.Panel.__init__(self, *args, **kwargs)

        self.text_ctrl_pdf_note = wx.TextCtrl(parent=self, id=wx.ID_ANY,
                                              value="", style=wx.TE_MULTILINE)
        self.family_listctrl = wx.ListCtrl(parent=self, style=wx.LC_REPORT)
        self.button_generate_master = wx.Button(self, wx.ID_ANY, "Generate Master PDF...")
        self.button_generate_invoices = wx.Button(self, wx.ID_ANY, "Generate Invoices...")
        self.button_email_invoices = wx.Button(self, wx.ID_ANY, "Email Invoices...")

        self.family_provider = None
        self.fee_provider = None
        self.email_provider = None
        self.pdf_viewer = None

        self.error_msg = None
        # Used to keep track if it changed, because the IsModified() method doesn't seem
        # work properly with multi-line TextCtrl
        self.note_text = None

        self.__do_layout(border)

    def __do_layout(self, border):
        sizer_pdf_tab = wx.BoxSizer(wx.VERTICAL)

        label_note = wx.StaticText(self, wx.ID_ANY, "Note to add to PDF invoices:")
        sizer_pdf_tab.Add(label_note, 0, wx.ALL, border)
        sizer_pdf_tab.Add(self.text_ctrl_pdf_note, 1, wx.EXPAND | wx.ALL, border)

        sizer_pdf_tab.Add(self.family_listctrl, proportion=2, flag=wx.ALL | wx.EXPAND, border=border)

        sizer_pdf_buttons = wx.BoxSizer(wx.HORIZONTAL)
        sizer_pdf_buttons.Add(self.button_generate_master, 0, wx.ALL, border)
        self.Bind(wx.EVT_BUTTON, self.on_generate_master, self.button_generate_master)
        sizer_pdf_buttons.Add(self.button_generate_invoices, 0, wx.ALL, border)
        self.Bind(wx.EVT_BUTTON, self.on_generate_invoices, self.button_generate_invoices)
        sizer_pdf_buttons.Add(self.button_email_invoices, 0, wx.ALL, border)
        self.Bind(wx.EVT_BUTTON, self.on_email, self.button_email_invoices)
        sizer_pdf_tab.Add(sizer_pdf_buttons, 0, wx.ALL, border)

        self.SetSizer(sizer_pdf_tab)

        self.button_generate_master.Disable()
        self.button_generate_invoices.Disable()
        self.button_email_invoices.Disable()

    def close(self):
        if self.pdf_viewer is not None:
            self.pdf_viewer.Close()

    def get_name(self):
        return 'PDF'

    def set_family_provider(self, provider):
        self.family_provider = provider

    def set_fee_provider(self, provider):
        self.fee_provider = provider

    def set_email_provider(self, provider):
        self.email_provider = provider

    def enable_buttons(self, enable=True):
        self.button_generate_master.Enable()
        self.button_generate_invoices.Enable()
        self.button_email_invoices.Enable(enable)

    def on_generate_master(self, event=None):
        progress = wx.ProgressDialog("Generating Master PDF",
                                     "Please wait...\n\n"
                                     "Processing family:",
                                     parent=self,
                                     maximum=len(self.family_provider.get_families()),
                                     style=wx.PD_SMOOTH | wx.PD_APP_MODAL | wx.PD_ELAPSED_TIME | wx.PD_CAN_ABORT
                                     )
        # start_thread(self.generate_invoices, progress)
        progress.ShowModal()
        self.check_error()

    def on_generate_invoices(self, event=None):
        if self.pdf_viewer is not None:
            return
        pdf_buffer = MyBytesIO()
        try:
            families = self.family_provider.get_families()
            self.fee_provider.validate_fee_schedule(families)
            progress = wx.ProgressDialog("Generating Invoices",
                                         "Please wait...\n\n"
                                         "Generating invoice for family:",
                                         maximum=len(families), parent=self,
                                         style=wx.PD_SMOOTH | wx.PD_APP_MODAL | wx.PD_ELAPSED_TIME | wx.PD_CAN_ABORT
                                         )
            class_map = self.fee_provider.generate_class_map()
            note = self.text_ctrl_pdf_note.GetValue()
            start_thread(generate_invoices, families, class_map, note, pdf_buffer, progress)
            progress.ShowModal()
        except RuntimeError as e:
            logger.exception('error generating invoices')
            self.error_msg = f'error generating invoices: {e}'
        if not self.check_error():
            # Need to write to temporary file instead of passing the buffer object directly, or
            # else the PDFViewer "Save As" button does not work.
            tmp_file = tempfile.NamedTemporaryFile()
            tmp_file.write(pdf_buffer.getvalue())
            tmp_file.flush()
            pdf_buffer.seek(0)
            self.pdf_viewer = PDFViewer(None, size=(800, 600))
            self.pdf_viewer.viewer.LoadFile(tmp_file.name)
            self.pdf_viewer.Show()

    def on_email(self, event=None):
        subject = self.email_provider.text_ctrl_email_subject.GetValue()
        body = self.email_provider.text_ctrl_email_body.GetValue()
        try:
            if not subject.strip():
                self.error_msg = 'Email subject may not be empty. Please enter one in' \
                                 ' the Email Setup tab before sending email.'
            elif not body.strip():
                self.error_msg = 'Email message body may not be empty. Please enter' \
                                 ' one in the Email Setup tab before sending email.'
            elif check_credentials(parent=self, no_action_popup=False):
                self.ask_to_send_email(subject, body)
            self.check_error()
        except Exception as e:
            self.error_msg = f'Error while sending email: {e}'
            logger.exception('could not send mail')
        self.check_error()

    def ask_to_send_email(self, subject, body):
        msg = 'Do you wish to send the emails now, or save the emails to' \
              ' the drafts folder, so you can review them and send them later?'
        caption = 'Choose Email Action'
        dlg = wx.MessageDialog(parent=self,
                               message=msg,
                               caption=caption,
                               style=wx.YES | wx.NO | wx.YES_DEFAULT | wx.CANCEL)
        dlg.SetYesNoCancelLabels('Save as drafts', 'Send now', 'Cancel')
        response = dlg.ShowModal()
        if response == wx.ID_YES:
            logger.debug('save as drafts')
            self.create_drafts_dialog(subject, body)
        elif response == wx.ID_NO:
            logger.debug('send now')
        else:
            logger.debug('cancel')
        dlg.Destroy()

    def create_drafts_dialog(self, subject, body):
        progress = wx.ProgressDialog(
            parent=self,
            title='Emailing Invoices',
            message="Please wait...\n\n"
                    "Emailing invoice for family:",
            maximum=len(self.family_provider.get_families()),
            style=wx.PD_SMOOTH | wx.PD_APP_MODAL | wx.PD_ELAPSED_TIME | wx.PD_CAN_ABORT)
        start_thread(self.create_drafts_thread, subject, body, progress)
        progress.ShowModal()

    def create_drafts_thread(self, subject, body, progress):
        try:
            families = self.family_provider.get_families()
            self.fee_provider.validate_fee_schedule(families)
            gmail.create_drafts(subject, body,
                                families,
                                self.fee_provider.generate_class_map(),
                                progress)
        except KeyError as e:
            self.error_msg = "Missing teacher or fee for class while sending email: " + e.args[0]

        except Exception as e:
            self.error_msg = "Error while sending email: " + str(e)
            logger.exception('could not send email')
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

    def get_data(self):
        return {
            'note': self.text_ctrl_pdf_note.GetValue(),
        }

    def load_data(self, data=None):
        if 'note' in data:
            self.text_ctrl_pdf_note.SetValue(data['note'])
        self.populate_family_list()

    def populate_family_list(self):
        # The following assumes the family_provider has already been populated with data
        self.family_listctrl.DeleteAllItems()
        self.family_listctrl.DeleteAllColumns()
        self.family_listctrl.InsertColumn(0, 'Family Name')
        self.family_listctrl.InsertColumn(1, 'Num Parents')
        self.family_listctrl.InsertColumn(2, 'Num Students')
        total_parents = 0
        total_emails = 0
        total_students = 0
        for r, family in enumerate(self.family_provider.get_families().values()):
            last_names = set()
            num_parents = 0
            num_emails = 0
            num_students = 0
            for parent in family['parents']:
                num_parents += 1
                if parent[Column.EMAIL]:
                    num_emails += 1
                last_names.add(parent[Column.LAST_NAME])
            for student in family['students']:
                num_students += 1
                last_names.add(student[Column.LAST_NAME])
            self.family_listctrl.InsertItem(r, '/'.join(sorted(last_names)))
            self.family_listctrl.SetItem(r, 1, str(num_parents))
            self.family_listctrl.SetItem(r, 2, str(num_students))
            total_parents += num_parents
            total_emails += num_emails
            total_students += num_students
        for c in range(3):
            self.family_listctrl.SetColumnWidth(c, wx.LIST_AUTOSIZE_USEHEADER)

    def is_modified(self):
        return self.text_ctrl_pdf_note.GetValue() != self.note_text

    def clear_is_modified(self):
        self.note_text = self.text_ctrl_pdf_note.GetValue()
