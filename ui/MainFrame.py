import logging
import pickle

import wx

import app_config
import ui.ApplicationPanel
import ui.menu.EditMenu
import ui.menu.FileMenu
import ui.menu.HelpMenu

SAVE_SUFFIX = '.classinvoice'

SAVE_FORMAT_VERSION = 1.0

logger = logging.getLogger(f'classinvoices.{__name__}')


class MainFrame(wx.Frame):
    """Main Frame holding the Panel."""

    DEFAULT_SIZE = (1080, 700)

    def __init__(self, *args, **kwargs):
        """Create the Frame."""
        wx.Frame.__init__(self, *args, **kwargs)

        # Add the Widget Panel
        self.application_panel = ui.ApplicationPanel(self, wx.ID_ANY)
        self.SetBackgroundColour('white')
        self.saved_filename = None

        # Build the menu bar
        menu_bar = wx.MenuBar()
        self.file_menu = ui.menu.FileMenu(parent=self)
        menu_bar.Append(self.file_menu, '&File')
        # menu_bar.Append(ui.menu.EditMenu(parent=self), '&Edit')
        self.help_menu = ui.menu.HelpMenu()
        menu_bar.Append(self.help_menu, '&Help')
        self.SetMenuBar(menu_bar)

        # Add a status bar at the bottom of the frame
        self.CreateStatusBar()
        self.SetStatusText('Ready to open registration CSV file')

        self.Fit()
        self.SetMinSize((900, 500))

        self.Bind(wx.EVT_CLOSE, self.on_close)

        self.error_msg = None
        self.modified = False
        self.clear_is_modified()

        if self.file_menu.file_history.GetCount() > 0:
            path = self.file_menu.file_history.GetHistoryFile(0)
            try:
                self.load_file(path)
            except (OSError, FileNotFoundError) as e:
                self.error_msg = f'Could not load file {path}: {e}'
        self.check_error()

    def is_modified(self):
        return self.modified or self.application_panel.is_modified()

    def clear_is_modified(self):
        self.modified = False
        self.application_panel.clear_is_modified()

    def on_new(self, event=None):
        if not self.is_safe_to_close():
            return
        self.error_msg = None
        self.saved_filename = None
        self.SetTitle(app_config.APP_NAME)
        self.SetSize(self.DEFAULT_SIZE)
        self.application_panel.load_data({})
        self.clear_is_modified()

    def on_open(self, event=None):
        if not self.is_safe_to_close():
            return
        dirname = ''
        file_dialog = wx.FileDialog(parent=None,
                                    message='Choose a ClassInvoices file',
                                    defaultDir=dirname,
                                    defaultFile='',
                                    wildcard=f'*{SAVE_SUFFIX}',
                                    style=wx.FD_OPEN)
        if file_dialog.ShowModal() == wx.ID_OK:
            path = file_dialog.GetPath()
            self.load_file(path)
        file_dialog.Destroy()
        self.check_error()

    def check_modified_load_file(self, path):
        if not self.is_safe_to_close():
            return
        self.load_file(path)

    def load_file(self, path):
        try:
            with open(path, 'rb') as f:
                data = pickle.load(f)
            self.update_file_history(path)
            self.load_data(data)
            self.saved_filename = path
            self.SetTitle(path)
        except Exception as e:
            self.error_msg = f'Could not load file: {e}'
        self.check_error()

    def load_data(self, data):
        if data['version'] <= SAVE_FORMAT_VERSION:
            self.SetPosition(data['position'])
            self.SetSize(data['size'])
            self.application_panel.load_data(data['application_panel'])
            self.clear_is_modified()

    def on_save(self, event=None):
        path = None
        try:
            doc = self.get_data()
            path = self.get_save_path(event.GetId())
            if path is not None:
                with open(path, 'wb') as f:
                    pickle.dump(doc, f)
                self.update_file_history(path)
                self.clear_is_modified()
                self.saved_filename = path
                self.SetTitle(path)
                self.SetStatusText(f'Saved to {path}')
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
                                        defaultFile=f'Class Invoices{SAVE_SUFFIX}',
                                        wildcard=f'*{SAVE_SUFFIX}',
                                        style=wx.FD_SAVE)
            if file_dialog.ShowModal() == wx.ID_OK:
                path = file_dialog.GetPath()
                if not path.endswith(SAVE_SUFFIX):
                    path += SAVE_SUFFIX
            file_dialog.Destroy()
            self.check_error()
        return path

    def update_file_history(self, path):
        self.file_menu.file_history.AddFileToHistory(path)
        self.file_menu.file_history.Save(app_config.conf)
        app_config.conf.Flush()

    def on_close(self, event=None):
        # First check if the active window is the log window
        if self.help_menu.log_window and self.help_menu.log_window.IsActive():
            self.help_menu.on_close_log()
        elif not self.IsActive():
            # One of the sub windows must be active. Find it and close it.
            self.application_panel.close_sub_window()
        else:
            # TODO: this should really do a "new document" action
            self.on_quit()

    def on_quit(self, event=None):
        # Make sure any log window is closed, ore else it will prevent the app from exiting
        self.help_menu.on_close_log()
        if self.is_safe_to_close():
            self.application_panel.close()
            self.Destroy()

    def check_error(self):
        if self.error_msg:
            caption = 'Error'
            dlg = wx.MessageDialog(self, self.error_msg,
                                   caption, wx.OK | wx.ICON_WARNING)
            self.error_msg = None
            dlg.ShowModal()
            dlg.Destroy()

    def is_safe_to_close(self):
        """Check if we can safely discard the contents of the frame.
        If any data is modified, display a popup asking the user to continue or cancel.
        Returns True if there are no changes, or the user chose to discard changes."""
        if not self.is_modified():
            return True
        dlg = wx.MessageDialog(parent=self,
                               message='Unsaved changes will be lost if you continue.',
                               caption='Discard Changes?',
                               style=wx.OK | wx.CANCEL | wx.ICON_QUESTION | wx.CANCEL_DEFAULT)
        dlg.SetOKLabel('Discard Changes')
        result = dlg.ShowModal()
        dlg.Destroy()
        return result == wx.ID_OK
