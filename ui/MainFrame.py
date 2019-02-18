import os

import wx

import ui.DemoPanel
from ui.menu.FileMenu import FileMenu


class MainFrame(wx.Frame):
    """Main Frame holding the Panel."""

    def __init__(self, *args, **kwargs):
        """Create the DemoFrame."""
        wx.Frame.__init__(self, *args, **kwargs)

        # Build the menu bar
        menu_bar = wx.MenuBar()
        menu_bar.Append(FileMenu(self), "&File")
        self.SetMenuBar(menu_bar)

        # Add the Widget Panel
        self.Panel = ui.DemoPanel.DemoPanel(self)

        # Add a status bar at the bottom of the frame
        self.CreateStatusBar()
        self.SetStatusText("Ready to open new CSV file")

        self.Fit()
