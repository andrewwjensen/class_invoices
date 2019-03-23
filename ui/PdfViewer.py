import wx
import wx.lib.sized_controls as sc

from wx.lib.pdfviewer import pdfViewer, pdfButtonPanel


class PdfViewer(sc.SizedFrame):
    def __init__(self, parent, **kwds):
        super(PdfViewer, self).__init__(parent, **kwds)

        pane_contents = self.GetContentsPane()
        self.button_panel = pdfButtonPanel(pane_contents, wx.ID_ANY,
                                           wx.DefaultPosition, wx.DefaultSize, 0)
        self.button_panel.SetSizerProps(expand=True)
        self.viewer = pdfViewer(pane_contents, wx.ID_ANY, wx.DefaultPosition,
                                wx.DefaultSize,
                                wx.HSCROLL | wx.VSCROLL | wx.SUNKEN_BORDER)

        self.viewer.SetSizerProps(expand=True, proportion=1)

        # introduce button_panel and viewer to each other
        self.button_panel.viewer = self.viewer
        self.viewer.buttonpanel = self.button_panel
