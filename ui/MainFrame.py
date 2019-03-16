import wx

import ui.ApplicationPanel
import ui.menu.EditMenu
import ui.menu.FileMenu
import ui.menu.HelpMenu


class MainFrame(wx.Frame):
    """Main Frame holding the Panel."""

    def __init__(self, *args, **kwargs):
        """Create the Frame."""
        kwargs["style"] = kwargs.get("style", 0) | wx.DEFAULT_FRAME_STYLE
        wx.Frame.__init__(self, *args, **kwargs)

        # Add the Widget Panel
        self.application_panel = ui.ApplicationPanel(self, wx.ID_ANY)
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

    def set_splitter_width(self):
        width = self.application_panel.splitter.GetSize()[0]
        self.application_panel.splitter.SetSashPosition(width / 2)

    def on_open(self):
        print('open')

    def on_save(self):
        print('save')

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
