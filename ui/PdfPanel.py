import logging
import tempfile

import wx
import wx.lib.newevent

from mail import gmail
from mail.gmail import check_credentials
from model.columns import Column
from pdf.generate import generate_invoices, generate_master
from ui.PdfViewer import PdfViewer
from util import MyBytesIO, PROGRESS_STYLE

DEFAULT_BORDER = 5

logger = logging.getLogger(f'classinvoices.{__name__}')


def confirm_send_email(sending_drafts, families):
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
    dlg = wx.MessageDialog(parent=None,
                           message=msg,
                           caption=caption,
                           style=wx.OK | wx.CANCEL | wx.CANCEL_DEFAULT)
    dlg.SetOKLabel(ok_label)
    response = dlg.ShowModal()
    return response == wx.ID_OK


class PdfPanel(wx.Panel):

    def __init__(self, tempdir, border=DEFAULT_BORDER, *args, **kwargs):
        wx.Panel.__init__(self, *args, **kwargs)

        self.text_ctrl_term = wx.TextCtrl(parent=self, size=(5000, 23))
        self.text_ctrl_pdf_note = wx.TextCtrl(parent=self, style=wx.TE_MULTILINE)
        self.text_ctrl_pdf_note.MacCheckSpelling(True)
        self.family_listctrl = wx.ListCtrl(parent=self, style=wx.LC_REPORT)
        self.button_generate_master = wx.Button(self, label='Preview Master PDF...')
        self.button_generate_invoices = wx.Button(self, label='Preview Invoices...')
        self.button_email_invoices = wx.Button(self, label='Email Invoices...')

        # Create temp files here. The temp dir will be deleted when the application closes.
        self.tempdir = tempdir

        self.family_provider = None
        self.fee_provider = None
        self.email_provider = None

        # Keep reference to all opened PDF viewers so we can close the windows on exit
        self.pdf_viewers = set()

        # Map row number in family table to family_id, which indexes families map
        self.row_to_family_id = {}

        self.error_msg = None
        self.draft_ids = []

        # Used to keep track if it changed, because the IsModified() method doesn't seem
        # work properly with multi-line TextCtrl
        self.term_text = None
        self.note_text = None

        self.__do_layout(border)

    def __do_layout(self, border):
        sizer_pdf_tab = wx.BoxSizer(wx.VERTICAL)
        sizer_term_row = wx.BoxSizer(wx.HORIZONTAL)

        label_subject = wx.StaticText(self, label='Term:')
        sizer_term_row.Add(label_subject, proportion=0)
        sizer_term_row.Add(self.text_ctrl_term, proportion=1)
        sizer_pdf_tab.Add(sizer_term_row, proportion=0, flag=wx.LEFT | wx.TOP | wx.RIGHT, border=border)

        label_note = wx.StaticText(self, label='Note to add to PDF invoices:')
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

    ################################################################################################
    # PDF generation methods
    ################################################################################################

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
        """
        Called by wxPython when the generate invoices button is clicked.
        Args:
          event (wx.Event): wxPython event
        """
        pdf_buffer = MyBytesIO()
        try:
            families = self.get_selected_families()
            self.fee_provider.validate_fee_schedule(families)
            class_map = self.fee_provider.generate_class_map()
            note = self.text_ctrl_pdf_note.GetValue()
            term = self.text_ctrl_term.GetValue()

            progress = wx.ProgressDialog('Generating Invoices',
                                         'Please wait...\n\n'
                                         'Generating invoice for family:',
                                         maximum=len(families),
                                         style=PROGRESS_STYLE)
            generate_invoices(progress, families, class_map, note, term, pdf_buffer)
            progress.Update(progress.GetRange())  # Make sure progress dialog closes
            self.open_pdf_viewer(pdf_buffer)
        except RuntimeError as e:
            logger.exception('error generating invoices')
            self.error_msg = f'error generating invoices: {e}'

    def open_pdf_viewer(self, pdf_buffer):
        """Display the given pdf_buffer in a new PDF viewer window.
        Uses wxPython's lib.pdfviewer module.
        Args:
            pdf_buffer (io.BytesIO): A buffer containing the PDF data.
        """

        # Need to write to temporary file instead of passing the buffer object directly, or
        # else the PdfViewer "Save As" button does not work. Also, keep them open so they don't
        # get deleted until we close the window.
        (fd, path) = tempfile.mkstemp(dir=self.tempdir, suffix='.PDF')
        logger.debug(f'pdf size: {len(pdf_buffer.getvalue())}')
        with open(fd, 'wb') as tmp_file:
            tmp_file.write(pdf_buffer.getvalue())
            tmp_file.flush()

        pdf_viewer = PdfViewer(None, size=(800, 1000))
        self.pdf_viewers.add(pdf_viewer)
        logger.debug(f'loading PDF {path}', extra={'pdf_filename': path})
        pdf_viewer.viewer.LoadFile(path)
        pdf_viewer.Show()
        pdf_viewer.Raise()
        pdf_viewer.Bind(wx.EVT_CLOSE, self.on_close_sub_window)

    ################################################################################################
    # Sending email methods
    ################################################################################################

    def on_email(self, event=None):
        """
        Called by wxPython when the email button is clicked.
        Args:
          event (wx.Event): wxPython event
        """
        subject = self.email_provider.text_ctrl_email_subject.GetValue()
        body = self.email_provider.text_ctrl_email_body.GetValue()
        try:
            if not subject.strip():
                self.error_msg = 'Email subject may not be empty. Please enter one in' \
                                 ' the Email Setup tab before sending email.'
            elif not body.strip():
                self.error_msg = 'Email message body may not be empty. Please enter' \
                                 ' one in the Email Setup tab before sending email.'
            elif check_credentials(parent=self, show_popup_if_no_action_needed=False):
                self.choose_draft_or_send(subject, body)
        except Exception as e:
            self.error_msg = f'Error while sending email: {e}'
            logger.exception('could not send mail')
        self.check_error()

    def choose_draft_or_send(self, subject, body):
        """
        Prompt user to send email now, create drafts, or cancel.
        :str subject: Subject of email
        :str body: Message body of email
        """
        msg = 'Do you wish to send the emails now, or save the emails to' \
              ' the drafts folder, so you can review them and send them later?'
        caption = 'Choose Email Action'
        dlg = wx.MessageDialog(parent=None,
                               message=msg,
                               caption=caption,
                               style=wx.YES | wx.NO | wx.CANCEL | wx.YES_DEFAULT)
        dlg.SetYesNoLabels('Save as drafts', 'Send now')
        response = dlg.ShowModal()
        if response != wx.ID_CANCEL:
            families = self.get_selected_families()
            sending_drafts = response == wx.ID_YES
            if confirm_send_email(sending_drafts, families):
                if sending_drafts:
                    self.create_drafts(families, subject, body)
                    if not self.error_msg:
                        self.send_drafts_dialog(self.draft_ids)
                else:
                    self.send_email(families, subject, body)
        dlg.Destroy()

    def send_email(self, families, subject, body):
        progress = wx.ProgressDialog(
            title='Emailing Invoices',
            message='Please wait...\n\n'
                    'Emailing invoice for family: ',
            maximum=len(families),
            style=PROGRESS_STYLE)
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
            progress.Update(progress.GetRange())  # Make sure progress dialog closes
        except KeyError as e:
            self.error_msg = f'Missing teacher or fee for class while sending email: {e.args[0]}'

        except Exception as e:
            self.error_msg = f'Error while sending email: {e}'
            logger.exception('could not send email')

    #################################################################################################
    # Creating drafts methods
    #################################################################################################

    def create_drafts(self, families, subject, body):
        progress = wx.ProgressDialog(
            title='Create Draft Emails',
            message='Please wait...\n\n'
                    'Creating draft email for family: ',
            maximum=len(families),
            style=PROGRESS_STYLE)
        self.draft_ids = []
        try:
            self.fee_provider.validate_fee_schedule(families)
            note = self.text_ctrl_pdf_note.GetValue()
            term = self.text_ctrl_term.GetValue()
            class_map = self.fee_provider.generate_class_map()
            self.draft_ids = gmail.create_drafts(subject,
                                                 body,
                                                 'bcc',
                                                 families,
                                                 class_map,
                                                 note,
                                                 term,
                                                 progress)
            progress.Update(progress.GetRange())  # Make sure progress dialog closes
        except KeyError as e:
            self.error_msg = 'Missing teacher or fee for class while creating drafts: ' + e.args[0]
        except Exception as e:
            self.error_msg = f'Error while creating drafts: {e}'
            logger.exception('could not create drafts')

    ################################################################################################
    # Sending drafts methods
    ################################################################################################

    def send_drafts(self, draft_ids):
        progress = wx.ProgressDialog(
            title='Send Draft Emails',
            message='Please wait...\n\n'
                    'Sending draft',
            maximum=len(draft_ids),
            style=PROGRESS_STYLE)
        try:
            gmail.send_drafts(draft_ids, progress)
            progress.Update(progress.GetRange())  # Make sure progress dialog closes
        except Exception as e:
            self.error_msg = f'Error while sending drafts: {e}'
            logger.exception('could not send drafts')

    def send_drafts_dialog(self, draft_ids):
        caption = 'Send Drafts?'
        msg = 'Check your Gmail drafts folder to verify the messages are correct\n\n' \
              'You may then send them manually through Gmail, or send them all at once here.'
        dlg = wx.MessageDialog(parent=None,
                               message=msg,
                               caption=caption,
                               style=wx.OK | wx.CANCEL)
        plural = 's'
        if len(draft_ids) == 1:
            plural = ''
        dlg.SetOKCancelLabels(ok='Send Manually Later',
                              cancel=f'Send {len(draft_ids)} Draft{plural} Now')
        response = dlg.ShowModal()
        if response == wx.ID_CANCEL:
            self.send_drafts(draft_ids)

    ################################################################################################
    # Other methods
    ################################################################################################

    def check_error(self):
        if self.error_msg:
            caption = 'Error'
            dlg = wx.MessageDialog(parent=None,
                                   message=self.error_msg,
                                   caption=caption,
                                   style=wx.OK | wx.ICON_WARNING)
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
        self.family_listctrl.InsertColumn(1, 'Parents')
        self.family_listctrl.InsertColumn(2, 'Students')
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
        self.family_listctrl.SetColumnWidth(0, wx.LIST_AUTOSIZE_USEHEADER)
        self.family_listctrl.SetColumnWidth(1, 75)
        self.family_listctrl.SetColumnWidth(2, 75)

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
