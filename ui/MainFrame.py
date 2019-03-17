import pickle
import traceback

import wx

import ui.ApplicationPanel
import ui.menu.EditMenu
import ui.menu.FileMenu
import ui.menu.HelpMenu

SAVE_FORMAT_VERSION = 1.0


class MainFrame(wx.Frame):
    """Main Frame holding the Panel."""

    def __init__(self, *args, **kwargs):
        """Create the Frame."""
        kwargs["style"] = kwargs.get("style", 0) | wx.DEFAULT_FRAME_STYLE
        wx.Frame.__init__(self, *args, **kwargs)

        # Add the Widget Panel
        self.application_panel = ui.ApplicationPanel(self, wx.ID_ANY)
        self.application_panel.load_test_data()
        self.SetBackgroundColour('white')

        # Build the menu bar
        menu_bar = wx.MenuBar()
        menu_bar.Append(ui.menu.FileMenu(self), "&File")
        # menu_bar.Append(ui.menu.EditMenu(self), "&Edit")
        menu_bar.Append(ui.menu.HelpMenu(self), "&Help")
        self.SetMenuBar(menu_bar)

        # Add a status bar at the bottom of the frame
        self.CreateStatusBar()
        self.SetStatusText("Ready to open registration CSV file")

        self.Fit()
        self.SetMinSize(size=(600, 400))

        self.Bind(wx.EVT_CLOSE, self.on_close)

        self.error_msg = None
        self.modified = False

    def set_splitter_width(self):
        width = self.application_panel.splitter.GetSize()[0]
        self.application_panel.splitter.SetSashPosition(width / 2)

    def on_open(self, event=None):
        dirname = ''
        file_dialog = wx.FileDialog(parent=self,
                                    message="Choose a ClassInvoices file",
                                    defaultDir=dirname,
                                    defaultFile="",
                                    wildcard="*.classinvoice",
                                    style=wx.FD_OPEN)
        if file_dialog.ShowModal() == wx.ID_OK:
            try:
                with open(file_dialog.GetPath(), 'rb') as f:
                    data = pickle.load(f)
                self.load_data(data)
            except Exception as e:
                self.error_msg = "Error while reading fee schedule: " + str(e)
                traceback.print_exc()
        file_dialog.Destroy()
        self.check_error()

    def on_save(self, event=None):
        doc = self.get_data()
        dirname = ''
        file_dialog = wx.FileDialog(parent=self,
                                    message="Save ClassInvoices file",
                                    defaultDir=dirname,
                                    defaultFile="",
                                    wildcard="*.classinvoice",
                                    style=wx.FD_SAVE)
        if file_dialog.ShowModal() == wx.ID_OK:
            try:
                print(type(file_dialog.GetPath()), file_dialog.GetPath())
                with open(file_dialog.GetPath(), 'wb') as f:
                    pickle.dump(doc, f)
            except Exception as e:
                self.error_msg = "Error while exporting fee schedule: " + str(e)
                traceback.print_exc()
        file_dialog.Destroy()
        self.check_error()

    def get_data(self):
        return {
            'version': SAVE_FORMAT_VERSION,
            'position': self.GetPosition(),
            'size': self.GetSize(),
            'application_panel': self.application_panel.get_data()
        }

    def load_data(self, data):
        if data['version'] <= SAVE_FORMAT_VERSION:
            self.SetPosition(data['position'])
            self.SetSize(data['size'])
            self.application_panel.load_data(data['application_panel'])
            self.application_panel.set_is_modified(False)

    def on_close(self, event=None):
        if not self.application_panel.is_modified():
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

    def check_error(self):
        if self.error_msg:
            caption = 'Error'
            dlg = wx.MessageDialog(self, self.error_msg,
                                   caption, wx.OK | wx.ICON_WARNING)
            self.error_msg = None
            dlg.ShowModal()
            dlg.Destroy()
