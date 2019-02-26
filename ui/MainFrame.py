import wx

import ui.DataPanel
from ui.menu.FileMenu import FileMenu
from ui.menu.HelpMenu import HelpMenu


class MainFrame(wx.Frame):
    """Main Frame holding the Panel."""

    def __init__(self, *args, **kwargs):
        """Create the Frame."""
        wx.Frame.__init__(self, *args, **kwargs)

        # Add the Widget Panel
        self.data_panel = ui.DataPanel.DataPanel(self, wx.ID_ANY)

        # Build the menu bar
        menu_bar = wx.MenuBar()
        menu_bar.Append(FileMenu(self, self.data_panel), "&File")
        menu_bar.Append(HelpMenu(self), "&Help")
        self.SetMenuBar(menu_bar)

        # Add a status bar at the bottom of the frame
        self.CreateStatusBar()
        self.SetStatusText("Ready to open registration CSV file")

        self.Fit()
