import logging
import pickle

import wx

import app_config
import ui.ApplicationPanel
import ui.menu.EditMenu
import ui.menu.FileMenu
import ui.menu.HelpMenu

SAVE_FORMAT_VERSION = 1.0

logging.basicConfig()
logger = logging.getLogger(app_config.APP_NAME)
logger.setLevel(logging.INFO)


class MainFrame(wx.Frame):
    """Main Frame holding the Panel."""

    def __init__(self, *args, **kwargs):
        """Create the Frame."""
        kwargs["style"] = kwargs.get("style", 0) | wx.DEFAULT_FRAME_STYLE
        wx.Frame.__init__(self, *args, **kwargs)

        # Add the Widget Panel
        self.application_panel = ui.ApplicationPanel(self, wx.ID_ANY)
        self.SetBackgroundColour('white')
        self.saved_filename = None

        # Build the menu bar
        menu_bar = wx.MenuBar()
        self.file_menu = ui.menu.FileMenu(self)
        menu_bar.Append(self.file_menu, "&File")
        # menu_bar.Append(ui.menu.EditMenu(self), "&Edit")
        menu_bar.Append(ui.menu.HelpMenu(self), "&Help")
        self.SetMenuBar(menu_bar)

        # Add a status bar at the bottom of the frame
        self.CreateStatusBar()
        self.SetStatusText("Ready to open registration CSV file")

        self.Fit()
        self.SetMinSize(size=(600, 400))

        self.Bind(wx.EVT_CLOSE, self.on_close)
        self.Bind(wx.EVT_MOVE, self.on_change)
        self.Bind(wx.EVT_SIZE, self.on_change)

        self.error_msg = None
        self.modified = False

        if self.file_menu.file_history.GetCount() > 0:
            self.load_file(self.file_menu.file_history.GetHistoryFile(0))

    def is_modified(self):
        return self.modified or self.application_panel.is_modified()

    def set_is_modified(self, modified=True):
        self.modified = modified
        self.application_panel.set_is_modified(modified)

    def on_open(self, event=None):
        dirname = ''
        file_dialog = wx.FileDialog(parent=self,
                                    message="Choose a ClassInvoices file",
                                    defaultDir=dirname,
                                    defaultFile="",
                                    wildcard="*.classinvoice",
                                    style=wx.FD_OPEN)
        if file_dialog.ShowModal() == wx.ID_OK:
            path = file_dialog.GetPath()
            try:
                self.load_file(path)
            except Exception as e:
                self.error_msg = f'Error opening {path}: {e}'
                logger.exception('Open error')
        file_dialog.Destroy()
        self.check_error()

    def load_file(self, path):
        with open(path, 'rb') as f:
            data = pickle.load(f)
        self.update_file_history(path)
        self.load_data(data)
        self.saved_filename = path
        self.SetTitle(path)

    def load_data(self, data):
        if data['version'] <= SAVE_FORMAT_VERSION:
            self.SetPosition(data['position'])
            self.SetSize(data['size'])
            self.application_panel.load_data(data['application_panel'])
            self.set_is_modified(False)

    def on_save(self, event=None):
        path = None
        try:
            doc = self.get_data()
            path = self.get_save_path(event.GetId())
            if path is not None:
                with open(path, 'wb') as f:
                    pickle.dump(doc, f)
                self.update_file_history(path)
                self.set_is_modified(False)
                self.saved_filename = path
                self.SetTitle(path)
        except Exception as e:
            if path is None:
                self.error_msg = f'Error saving file: {e}'
            else:
                self.error_msg = f'Error saving {path}: {e}'
            logger.exception('Save error')
        self.check_error()

    def get_data(self):
        return {
            'version': SAVE_FORMAT_VERSION,
            'position': self.GetPosition(),
            'size': self.GetSize(),
            'application_panel': self.application_panel.get_data()
        }

    def get_save_path(self, event_id):
        path = None
        if event_id == wx.ID_SAVE:
            msg = 'Save ClassInvoices file'
        else:
            msg = 'Save a copy of ClassInvoices file as'
        if event_id == wx.ID_SAVE and self.saved_filename is not None:
            path = self.saved_filename
        else:
            # Don't have a saved filename, so prompt for where to save
            dirname = ''
            file_dialog = wx.FileDialog(parent=self,
                                        message=msg,
                                        defaultDir=dirname,
                                        defaultFile="",
                                        wildcard="*.classinvoice",
                                        style=wx.FD_SAVE)
            if file_dialog.ShowModal() == wx.ID_OK:
                path = file_dialog.GetPath()
            file_dialog.Destroy()
            self.check_error()
        return path

    def update_file_history(self, path):
        self.file_menu.file_history.AddFileToHistory(path)
        self.file_menu.file_history.Save(app_config.conf)
        app_config.conf.Flush()

    def on_close(self, event=None):
        if not self.is_modified():
            self.Destroy()
        else:
            dlg = wx.MessageDialog(parent=self,
                                   message="There are unsaved changes. Do you really want to close this application?",
                                   caption="Unsaved Changes",
                                   style=wx.OK | wx.CANCEL | wx.ICON_QUESTION | wx.CANCEL_DEFAULT)
            result = dlg.ShowModal()
            dlg.Destroy()
            if result == wx.ID_OK:
                self.Destroy()

    def on_change(self, event=None):
        self.modified = True
        event.Skip()

    def check_error(self):
        if self.error_msg:
            caption = 'Error'
            dlg = wx.MessageDialog(self, self.error_msg,
                                   caption, wx.OK | wx.ICON_WARNING)
            self.error_msg = None
            dlg.ShowModal()
            dlg.Destroy()
