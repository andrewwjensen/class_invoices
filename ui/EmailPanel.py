import logging

import wx
import wx.lib.newevent

import app_config
from mail.gmail import check_credentials

DEFAULT_BORDER = 5

logging.basicConfig()
logger = logging.getLogger(app_config.APP_NAME)
logger.setLevel(logging.INFO)


class EmailPanel(wx.Panel):

    def __init__(self, border=DEFAULT_BORDER, *args, **kwargs):
        wx.Panel.__init__(self, *args, **kwargs)

        self.button_set_up_email = wx.Button(self, wx.ID_ANY, "Set Up Gmail Connection...")
        self.text_ctrl_email_subject = wx.TextCtrl(self, wx.ID_ANY, "")
        self.text_ctrl_email_body = wx.TextCtrl(self, wx.ID_ANY, "", style=wx.TE_MULTILINE)

        self.error_msg = None
        # Used to keep track if it changed, because the IsModified() method doesn't seem
        # work properly with multi-line TextCtrl
        self.body_text = None

        self.__do_layout(border)

    def __do_layout(self, border):
        sizer_email_tab = wx.BoxSizer(wx.VERTICAL)
        sizer_email_tab_subject_row = wx.BoxSizer(wx.VERTICAL)
        sizer_email_tab_body_row = wx.BoxSizer(wx.VERTICAL)
        sizer_email_tab_button_row = wx.BoxSizer(wx.HORIZONTAL)

        label_subject = wx.StaticText(self, wx.ID_ANY, "Email Subject Line:")
        sizer_email_tab_subject_row.Add(label_subject, 0, wx.ALL, border)
        sizer_email_tab_subject_row.Add(self.text_ctrl_email_subject, proportion=1,
                                        flag=wx.EXPAND | wx.ALL, border=border)
        sizer_email_tab.Add(sizer_email_tab_subject_row, 0, wx.ALL, border)

        label_body = wx.StaticText(self, wx.ID_ANY, "Email Message Body:")
        sizer_email_tab_body_row.Add(label_body, 0, wx.ALL, border)
        sizer_email_tab_body_row.Add(self.text_ctrl_email_body, 1, wx.EXPAND | wx.ALL, border)
        sizer_email_tab.Add(sizer_email_tab_body_row, 1, wx.EXPAND | wx.ALL, border)

        sizer_email_tab_button_row.Add(self.button_set_up_email, 0, wx.ALL, border)
        self.Bind(wx.EVT_BUTTON, self.on_setup, self.button_set_up_email)
        sizer_email_tab.Add(sizer_email_tab_button_row, 0, wx.ALL, border)
        self.SetSizer(sizer_email_tab)

    def get_name(self):
        return 'Email Setup'

    def is_modified(self):
        body_is_modified = self.text_ctrl_email_body.GetValue() != self.body_text
        return body_is_modified or self.text_ctrl_email_subject.IsModified()

    def clear_is_modified(self):
        self.body_text = self.text_ctrl_email_body.GetValue()
        self.text_ctrl_email_subject.SetModified(False)

    def enable_buttons(self, enable=True):
        pass

    def on_setup(self, event=None):
        check_credentials(parent=self)
        self.check_error()

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
