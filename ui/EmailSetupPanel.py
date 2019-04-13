import logging

import wx
import wx.lib.newevent

import app_config
from mail.gmail import check_credentials

DEFAULT_BORDER = 5

logger = logging.getLogger(app_config.APP_NAME)


class EmailSetupPanel(wx.Panel):

    def __init__(self, border=DEFAULT_BORDER, *args, **kwargs):
        wx.Panel.__init__(self, *args, **kwargs)

        self.button_set_up_email = wx.Button(self, wx.ID_ANY, 'Set Up Gmail Connection...')
        self.text_ctrl_email_subject = wx.TextCtrl(self, wx.ID_ANY, '', size=(5000, 23))
        self.text_ctrl_email_body = wx.TextCtrl(self, wx.ID_ANY, '', style=wx.TE_MULTILINE)
        self.combo_cc_bcc = wx.Choice(self, choices=['None', 'Cc', 'Bcc'], )

        self.error_msg = None

        # Used to keep track if it changed, because the IsModified() method doesn't seem
        # work properly with multi-line TextCtrl, or if changes are in progress with
        # focus still in the text field.
        self.body_text_as_saved = None
        self.subject_text_as_saved = None
        self.save_cc_as_saved = None

        self.__do_layout(border)

    def __do_layout(self, border):
        sizer_email_tab = wx.BoxSizer(wx.VERTICAL)
        sizer_email_tab_cc_row = wx.BoxSizer(wx.HORIZONTAL)
        sizer_email_tab_subject_row = wx.BoxSizer(wx.VERTICAL)
        sizer_email_tab_body_row = wx.BoxSizer(wx.VERTICAL)
        sizer_email_tab_button_row = wx.BoxSizer(wx.HORIZONTAL)

        label_cc = wx.StaticText(self, wx.ID_ANY, '(B)cc myself?')
        sizer_email_tab_cc_row.Add(label_cc, proportion=0, flag=wx.LEFT | wx.TOP | wx.RIGHT, border=border)
        sizer_email_tab_cc_row.Add(self.combo_cc_bcc, proportion=0, flag=wx.LEFT | wx.TOP | wx.RIGHT, border=border)
        sizer_email_tab.Add(sizer_email_tab_cc_row, proportion=0, flag=wx.LEFT, border=border)

        label_subject = wx.StaticText(self, wx.ID_ANY, 'Email Subject Line:')
        sizer_email_tab_subject_row.Add(label_subject, proportion=0, flag=wx.LEFT | wx.TOP | wx.RIGHT, border=border)
        sizer_email_tab_subject_row.Add(self.text_ctrl_email_subject, proportion=0,
                                        flag=wx.EXPAND | wx.ALL, border=border)
        sizer_email_tab.Add(sizer_email_tab_subject_row, proportion=0, flag=wx.LEFT | wx.TOP | wx.RIGHT, border=border)

        label_body = wx.StaticText(self, wx.ID_ANY, 'Email Message Body:')
        sizer_email_tab_body_row.Add(label_body, proportion=0, flag=wx.LEFT | wx.TOP | wx.RIGHT, border=border)
        sizer_email_tab_body_row.Add(self.text_ctrl_email_body, proportion=1, flag=wx.EXPAND | wx.ALL, border=border)
        sizer_email_tab.Add(sizer_email_tab_body_row, proportion=1, flag=wx.EXPAND | wx.ALL, border=border)

        sizer_email_tab_button_row.Add(self.button_set_up_email, proportion=0, flag=wx.ALL, border=border)
        self.button_set_up_email.Bind(wx.EVT_BUTTON, self.on_setup)
        sizer_email_tab.Add(sizer_email_tab_button_row, proportion=0, flag=wx.ALL, border=border)
        self.SetSizer(sizer_email_tab)

    def get_name(self):
        return 'Email Setup'

    def is_modified(self):
        subject_is_modified = self.text_ctrl_email_subject.GetValue() != self.subject_text_as_saved
        body_is_modified = self.text_ctrl_email_body.GetValue() != self.body_text_as_saved
        cc_is_modified = self.combo_cc_bcc.GetSelection() != self.save_cc_as_saved
        return body_is_modified or cc_is_modified or subject_is_modified

    def clear_is_modified(self):
        self.subject_text_as_saved = self.text_ctrl_email_subject.GetValue()
        self.body_text_as_saved = self.text_ctrl_email_body.GetValue()
        self.save_cc_as_saved = self.combo_cc_bcc.GetSelection()

    def enable_buttons(self, enable=True):
        pass

    def on_setup(self, event=None):
        check_credentials(parent=self)
        self.check_error()

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
            'subject': self.text_ctrl_email_subject.GetValue(),
            'body': self.text_ctrl_email_body.GetValue(),
            'cc': self.combo_cc_bcc.GetSelection(),
        }

    def load_data(self, data):
        self.text_ctrl_email_subject.SetValue(data['subject'])
        self.text_ctrl_email_body.SetValue(data['body'])
        if 'cc' in data:
            self.combo_cc_bcc.SetSelection(data['cc'])
