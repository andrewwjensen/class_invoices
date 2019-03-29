import logging
import tempfile

import wx
import wx.lib.newevent

import app_config
from mail import gmail
from mail.gmail import check_credentials
from model.columns import Column
from pdf.generate import generate_invoices, generate_master
from ui.PdfViewer import PdfViewer
from util import start_thread, MyBytesIO

DEFAULT_BORDER = 5

logging.basicConfig()
logger = logging.getLogger(app_config.APP_NAME)
logger.setLevel(logging.INFO)


class PdfPanel(wx.Panel):

    def __init__(self, border=DEFAULT_BORDER, *args, **kwargs):
        wx.Panel.__init__(self, *args, **kwargs)

        self.text_ctrl_term = wx.TextCtrl(self, wx.ID_ANY, "", size=(5000, 30))
        self.text_ctrl_pdf_note = wx.TextCtrl(parent=self, id=wx.ID_ANY,
                                              value="", style=wx.TE_MULTILINE)
        self.family_listctrl = wx.ListCtrl(parent=self, style=wx.LC_REPORT)
        self.button_generate_master = wx.Button(self, wx.ID_ANY, "Preview Master PDF...")
        self.button_generate_invoices = wx.Button(self, wx.ID_ANY, "Preview Invoices...")
        self.button_email_invoices = wx.Button(self, wx.ID_ANY, "Email Invoices...")

        self.family_provider = None
        self.fee_provider = None
        self.email_provider = None

        # Keep reference to all opened PDF viewers so we can close the windows on exit
        self.pdf_viewers = set()

        # Keep reference to temp files open so they stay open and exist until exit
        self.temporary_files = set()

        # Map row number in family table to family_id, which indexes families map
        self.row_to_family_id = {}

        self.error_msg = None
        # Used to keep track if it changed, because the IsModified() method doesn't seem
        # work properly with multi-line TextCtrl
        self.term_text = None
        self.note_text = None

        self.__do_layout(border)

    def __do_layout(self, border):
        sizer_pdf_tab = wx.BoxSizer(wx.VERTICAL)
        sizer_term_row = wx.BoxSizer(wx.HORIZONTAL)

        label_subject = wx.StaticText(self, wx.ID_ANY, "Term:")
        sizer_term_row.Add(label_subject, proportion=0)
        sizer_term_row.Add(self.text_ctrl_term, proportion=1)
        sizer_pdf_tab.Add(sizer_term_row, proportion=0, flag=wx.LEFT | wx.TOP | wx.RIGHT, border=border)

        label_note = wx.StaticText(self, wx.ID_ANY, "Note to add to PDF invoices:")
        sizer_pdf_tab.Add(label_note, 0, wx.ALL, border)
        sizer_pdf_tab.Add(self.text_ctrl_pdf_note, 1, wx.EXPAND | wx.ALL, border)
        self.text_ctrl_pdf_note.SetMinSize((100, 100))

        sizer_pdf_tab.Add(self.family_listctrl, proportion=2, flag=wx.ALL | wx.EXPAND, border=border)
        self.family_listctrl.SetMinSize((100, 100))

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
        for viewer in self.pdf_viewers:
            try:
                viewer.Destroy()
            except RuntimeError:
                pass
        for f in self.temporary_files:
            f.close()

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

    def on_close_sub_window(self, event=None):
        self.pdf_viewers.remove(event.GetEventObject())
        event.Skip()

    def close_sub_window(self):
        for window in self.pdf_viewers:
            if window.IsActive():
                window.Close()
                break

    def on_generate_master(self, event=None):
        try:
            pdf_buffer = MyBytesIO()
            families = self.get_selected_families()
            if families:
                self.fee_provider.validate_fee_schedule(families)
                class_map = self.fee_provider.generate_class_map()
                term = self.text_ctrl_term.GetValue()
                generate_master(families, class_map, term, pdf_buffer)
                self.open_pdf_viewer(pdf_buffer)
        except RuntimeError as e:
            logger.exception('error generating master PDF')
            self.error_msg = f'error generating master PDF: {e}'

    def on_generate_invoices(self, event=None):
        pdf_buffer = MyBytesIO()
        try:
            families = self.get_selected_families()
            self.fee_provider.validate_fee_schedule(families)
            progress = wx.ProgressDialog("Generating Invoices",
                                         "Please wait...\n\n"
                                         "Generating invoice for family:",
                                         maximum=len(families), parent=self,
                                         style=wx.PD_SMOOTH | wx.PD_APP_MODAL | wx.PD_ELAPSED_TIME | wx.PD_CAN_ABORT
                                         )
            class_map = self.fee_provider.generate_class_map()
            note = self.text_ctrl_pdf_note.GetValue()
            term = self.text_ctrl_term.GetValue()
            start_thread(generate_invoices, families, class_map, note, term, pdf_buffer, progress)
            progress.ShowModal()
            self.open_pdf_viewer(pdf_buffer)
        except RuntimeError as e:
            logger.exception('error generating invoices')
            self.error_msg = f'error generating invoices: {e}'

    def open_pdf_viewer(self, pdf_buffer):
        # Need to write to temporary file instead of passing the buffer object directly, or
        # else the PdfViewer "Save As" button does not work. Also, keep them open so they don't
        # get deleted until we close the window.
        tmp_file = tempfile.NamedTemporaryFile()
        tmp_file.write(pdf_buffer.getvalue())
        tmp_file.flush()
        self.temporary_files.add(tmp_file)

        pdf_viewer = PdfViewer(None, size=(800, 1000))
        self.pdf_viewers.add(pdf_viewer)
        pdf_viewer.viewer.LoadFile(tmp_file.name)
        pdf_viewer.Show()
        pdf_viewer.Bind(wx.EVT_CLOSE, self.on_close_sub_window)

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
                self.choose_draft_or_send(subject, body)
        except Exception as e:
            self.error_msg = f'Error while sending email: {e}'
            logger.exception('could not send mail')
        self.check_error()

    def choose_draft_or_send(self, subject, body):
        msg = 'Do you wish to send the emails now, or save the emails to' \
              ' the drafts folder, so you can review them and send them later?'
        caption = 'Choose Email Action'
        dlg = wx.MessageDialog(parent=self,
                               message=msg,
                               caption=caption,
                               style=wx.YES | wx.NO | wx.CANCEL | wx.YES_DEFAULT)
        dlg.SetYesNoLabels('Save as drafts', 'Send now')
        response = dlg.ShowModal()
        if response != wx.ID_CANCEL:
            families = self.get_selected_families()
            sending_drafts = response == wx.ID_YES
            if self.confirm_send_email(sending_drafts, families):
                if sending_drafts:
                    self.create_drafts(families, subject, body)
                else:
                    self.send_email(families, subject, body)
        dlg.Destroy()

    def confirm_send_email(self, sending_drafts, families):
        num_families = len(families)
        num_addrs = 0
        for family in families.values():
            for parent in family['parents']:
                if parent[Column.EMAIL].strip():
                    num_addrs += 1
        caption = 'Confirm'
        if sending_drafts:
            msg = f'{num_families} email drafts to be sent to {num_addrs} email addresses will be created' \
                f' in the Drafts folder of your Gmail account. You may preview them before sending.'
            ok_label = 'Create Drafts'
        else:
            msg = f'{num_families} emails will be sent to {num_addrs} email addresses.'
            ok_label = 'Send Email Now'
        dlg = wx.MessageDialog(parent=self,
                               message=msg,
                               caption=caption,
                               style=wx.OK | wx.CANCEL | wx.CANCEL_DEFAULT)
        dlg.SetOKLabel(ok_label)
        response = dlg.ShowModal()
        return response == wx.ID_OK

    def send_email(self, families, subject, body):
        progress = wx.ProgressDialog(
            parent=self,
            title='Emailing Invoices',
            message="Please wait...\n\n"
                    "Emailing invoice for family: ",
            maximum=len(families),
            style=wx.PD_SMOOTH | wx.PD_APP_MODAL | wx.PD_ELAPSED_TIME | wx.PD_CAN_ABORT)
        start_thread(self.send_email_thread, families, subject, body, progress)
        progress.ShowModal()

    def send_email_thread(self, families, subject, body, progress):
        try:
            self.fee_provider.validate_fee_schedule(families)
            note = self.text_ctrl_pdf_note.GetValue()
            term = self.text_ctrl_term.GetValue()
            class_map = self.fee_provider.generate_class_map()
            gmail.send_emails(subject,
                              body,
                              'bcc',
                              families,
                              class_map,
                              note,
                              term,
                              progress)
        except KeyError as e:
            self.error_msg = "Missing teacher or fee for class while sending email: " + e.args[0]

        except Exception as e:
            self.error_msg = "Error while sending email: " + str(e)
            logger.exception('could not send email')
        wx.CallAfter(progress.EndModal, 0)
        wx.CallAfter(progress.Destroy)

    def create_drafts(self, families, subject, body):
        progress = wx.ProgressDialog(
            parent=self,
            title='Create Draft Emails',
            message="Please wait...\n\n"
                    "Creating draft email for family: ",
            maximum=len(families),
            style=wx.PD_SMOOTH | wx.PD_APP_MODAL | wx.PD_ELAPSED_TIME | wx.PD_CAN_ABORT)
        start_thread(self.create_drafts_thread, families, subject, body, progress)
        progress.ShowModal()

    def create_drafts_thread(self, families, subject, body, progress):
        draft_ids = []
        try:
            self.fee_provider.validate_fee_schedule(families)
            note = self.text_ctrl_pdf_note.GetValue()
            term = self.text_ctrl_term.GetValue()
            class_map = self.fee_provider.generate_class_map()
            draft_ids = gmail.create_drafts(subject,
                                            body,
                                            'bcc',
                                            families,
                                            class_map,
                                            note,
                                            term,
                                            progress)
        except KeyError as e:
            self.error_msg = "Missing teacher or fee for class while creating drafts: " + e.args[0]

        except Exception as e:
            self.error_msg = "Error while creating drafts: " + str(e)
            logger.exception('could not create drafts')
        wx.CallAfter(progress.EndModal, 0)
        wx.CallAfter(progress.Destroy)
        self.create_draft_send_dialog(draft_ids)

    def create_draft_send_dialog(self, draft_ids):
        pass

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
            'term': self.text_ctrl_term.GetValue(),
            'note': self.text_ctrl_pdf_note.GetValue(),
        }

    def load_data(self, data=None):
        if 'term' in data:
            self.text_ctrl_term.SetValue(data['term'])
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
        self.row_to_family_id = {}
        for r, family in enumerate(self.family_provider.get_families().values()):
            self.row_to_family_id[r] = family['id']
            last_names = set()
            num_parents = 0
            num_students = 0
            for parent in family['parents']:
                num_parents += 1
                last_names.add(parent[Column.LAST_NAME])
            for student in family['students']:
                num_students += 1
                last_names.add(student[Column.LAST_NAME])
            self.family_listctrl.InsertItem(r, '/'.join(sorted(last_names)))
            self.family_listctrl.SetItem(r, 1, str(num_parents))
            self.family_listctrl.SetItem(r, 2, str(num_students))
        for c in range(3):
            self.family_listctrl.SetColumnWidth(c, wx.LIST_AUTOSIZE_USEHEADER)

    def is_modified(self):
        term_modified = self.text_ctrl_term.GetValue() != self.term_text
        note_modified = self.text_ctrl_pdf_note.GetValue() != self.note_text
        return term_modified or note_modified

    def clear_is_modified(self):
        self.term_text = self.text_ctrl_term.GetValue()
        self.note_text = self.text_ctrl_pdf_note.GetValue()

    def get_selected_families(self):
        all_families = self.family_provider.get_families()
        if self.family_listctrl.SelectedItemCount == 0:
            return all_families
        families = {}
        r = self.family_listctrl.GetFirstSelected()
        while r != -1:
            family_id = self.row_to_family_id[r]
            families[family_id] = all_families[family_id]
            r = self.family_listctrl.GetNextSelected(r)
        return families
