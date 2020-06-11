import logging
import os

import wx

from ClassInvoices import ATTRIBUTION
from app_config import LOG_PATH

logger = logging.getLogger(f'classinvoices.{__name__}')


class LogPanel(wx.Panel):
    def __init__(self, parent=None):
        wx.Panel.__init__(self, parent)

        self.text = wx.TextCtrl(self, style=wx.TE_MULTILINE)
        self.text.SetEditable(False)
        btn = wx.Button(self, label='Refresh')
        btn.Bind(wx.EVT_BUTTON, self.refresh)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.text, 1, wx.ALL | wx.EXPAND)
        sizer.Add(btn, 0, wx.ALL | wx.CENTER, 5)

        self.SetSizer(sizer)

    def refresh(self, _event=None):
        path = LOG_PATH
        lines = []
        max_len = 1000
        if os.path.exists(path):
            with open(path) as f:
                self.text.Clear()
                for line in f:
                    lines.append(line)
                    if len(lines) > max_len:
                        lines.pop(0)
        for line in lines:
            self.text.WriteText(line)


class LogWindow(wx.Frame):
    def __init__(self):
        wx.Frame.__init__(self, None, title=LOG_PATH, size=(1200, 800))
        self.panel = LogPanel(self)
        self.Show()

    def refresh(self):
        self.panel.refresh()


class HelpMenu(wx.Menu):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        menu_about = self.Append(wx.ID_ABOUT, '&About ClassInvoices', 'About ClassInvoices')
        self.Bind(wx.EVT_MENU, self.on_about, menu_about)

        # --------------------
        self.AppendSeparator()
        self.AppendSeparator()

        menu_log_path = self.Append(wx.ID_ANY, '&Show Log', 'Show Log')
        self.Bind(wx.EVT_MENU, self.on_show_log, menu_log_path)
        self.log_window = None

    def on_about(self, _event=None):
        # A message dialog box with an OK button. wx.OK is a standard ID in wxWidgets.
        dlg = wx.MessageDialog(parent=None,
                               message='An application to generate PDF class invoices\n\n' + ATTRIBUTION,
                               caption='About ClassInvoices',
                               style=wx.OK)
        dlg.ShowModal()  # Show it
        dlg.Destroy()  # finally destroy it when finished.

    def on_show_log(self, _event=None):
        if self.log_window:
            self.log_window.Raise()
        else:
            self.log_window = LogWindow()
            self.log_window.Show()
            self.log_window.Bind(wx.EVT_CLOSE, self.on_close_log)
            self.log_window.refresh()

    def on_close_log(self, _event=None):
        if self.log_window:
            self.log_window.Destroy()
            self.log_window = None
