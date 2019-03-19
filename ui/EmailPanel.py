import logging
import time
import traceback

import wx
import wx.lib.newevent

import app_config
import mail.gmail as gmail
from util import start_thread

DEFAULT_BORDER = 5

logging.basicConfig()
logger = logging.getLogger(app_config.APP_NAME)
logger.setLevel(logging.INFO)


def check_for_cancel_thread(wait_dialog):
    try:
        while not wait_dialog.WasCancelled():
            time.sleep(0.1)  # prevent tight loop
        wx.CallAfter(wait_dialog.EndModal, 0)
        wx.CallAfter(wait_dialog.Destroy)
    except RuntimeError:
        # This will happen when the dialog is destroyed
        pass


class EmailPanel(wx.Panel):

    def __init__(self, border=DEFAULT_BORDER, *args, **kwargs):
        wx.Panel.__init__(self, *args, **kwargs)

        self.button_email_invoices = wx.Button(self, wx.ID_ANY, "Email Invoices...")
        self.text_ctrl_email_subject = wx.TextCtrl(self, wx.ID_ANY, "")
        self.text_ctrl_email_body = wx.TextCtrl(self, wx.ID_ANY, "", style=wx.TE_MULTILINE)

        self.family_provider = None
        self.fee_provider = None

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

    def set_family_provider(self, provider):
        self.family_provider = provider

    def set_fee_provider(self, provider):
        self.fee_provider = provider

    def enable_buttons(self, enable=True):
        self.button_email_invoices.Enable(enable)

    def on_email(self, event=None):
        subject = self.text_ctrl_email_subject.GetValue()
        body = self.text_ctrl_email_body.GetValue()
        try:
            if not subject.strip():
                self.error_msg = 'Email subject may not be empty.'
            elif not body.strip():
                self.error_msg = 'Enter a message body before sending email.'
            elif self.check_credentials():
                self.ask_to_send_email(subject, body)
        except Exception as e:
            self.error_msg = 'Error while sending email: ' + str(e)
            logger.exception('could not send mail')
        self.check_error()
        if not subject.strip():
            self.text_ctrl_email_subject.SetFocus()
        elif not body.strip():
            self.text_ctrl_email_body.SetFocus()

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
            traceback.print_exc()
        except Exception as e:
            self.error_msg = "Error while sending email: " + str(e)
            traceback.print_exc()
        wx.CallAfter(progress.EndModal, 0)
        wx.CallAfter(progress.Destroy)

    def check_error(self):
        if self.error_msg:
            caption = 'Error'
            dlg = wx.MessageDialog(parent=self,
                                   message=self.error_msg,
                                   caption=caption,
                                   style=wx.OK | wx.ICON_WARNING)
            self.error_msg = None
            dlg.ShowModal()
            dlg.Destroy()

    def get_data(self):
        return {
            'subject': self.text_ctrl_email_subject.GetValue(),
            'body': self.text_ctrl_email_body.GetValue(),
        }

    def load_data(self, data):
        self.text_ctrl_email_subject.SetValue(data['subject'])
        self.text_ctrl_email_body.SetValue(data['body'])

    def check_credentials(self):
        credentials = gmail.authenticate(connect_to_google=False)
        if credentials is None:
            msg = 'In order to use the email feature, you must have a Gmail account. You need to' \
                  ' log in to Google and authorize this app to send email on your' \
                  ' behalf. Do you wish to do this now? (You will be redirected to your browser)'
            caption = 'Google Authentication Required'
            dlg = wx.MessageDialog(parent=self,
                                   message=msg,
                                   caption=caption,
                                   style=wx.OK | wx.CANCEL)
            if dlg.ShowModal() == wx.ID_OK:
                dlg.Destroy()
                wx.Yield()  # Make sure dialog goes away before we open a new one
                wait_dialog = wx.ProgressDialog(
                    parent=self,
                    title='Waiting for response from Google...',
                    message='Respond to prompts in your browser. This\n'
                            'dialog will close automatically after you\n'
                            'approve or deny the authentication request.',
                    style=wx.PD_APP_MODAL | wx.PD_CAN_ABORT,
                    maximum=0,
                )
                wait_dialog.Pulse()
                start_thread(self.authenticate_with_google, wait_dialog)
                start_thread(check_for_cancel_thread, wait_dialog)
                wait_dialog.ShowModal()
                if self.error_msg:
                    self.check_error()
                    return False
                return True
            else:
                dlg.Destroy()
        return credentials is not None

    def authenticate_with_google(self, wait_dialog):
        self.error_msg = 'Unable to authorize. Please try again.'
        if gmail.authenticate():
            self.error_msg = None
        # The following will throw RuntimeError exceptions if the dialog has already
        # been destroyed by the progress thread (i.e. due to the user hitting the
        # Cancel button). But this is pretty harmless. It just displays a couple
        # tracebacks in the log.
        wx.CallAfter(wait_dialog.EndModal, 0)
        wx.CallAfter(wait_dialog.Destroy)
