import wx
import wx.lib.newevent

from pdf.generate import generate_invoices
from util import start_thread

DEFAULT_BORDER = 5


class PdfPanel(wx.Panel):

    def __init__(self, border=DEFAULT_BORDER, *args, **kwargs):
        wx.Panel.__init__(self, *args, **kwargs)

        self.button_generate_master = wx.Button(self, wx.ID_ANY, "Generate Master PDF...")
        self.button_generate_invoices = wx.Button(self, wx.ID_ANY, "Generate Invoices...")

        self.family_provider = None
        self.fee_provider = None

        self.modified = False
        self.error_msg = None

        self.__do_layout(border)

    def __do_layout(self, border):
        sizer_pdf_tab = wx.BoxSizer(wx.VERTICAL)

        sizer_pdf_tab.Add(self.button_generate_master, 0, wx.ALL, border)
        self.Bind(wx.EVT_BUTTON, self.on_generate_master, self.button_generate_master)
        sizer_pdf_tab.Add(self.button_generate_invoices, 0, wx.ALL, border)
        self.Bind(wx.EVT_BUTTON, self.on_generate_invoices, self.button_generate_invoices)
        self.SetSizer(sizer_pdf_tab)

        self.button_generate_master.Disable()
        self.button_generate_invoices.Disable()

    def get_name(self):
        return 'PDF'

    def is_modified(self):
        return self.modified

    def set_is_modified(self, modified=True):
        self.modified = modified

    def set_family_provider(self, provider):
        self.family_provider = provider

    def set_fee_provider(self, provider):
        self.fee_provider = provider

    def enable_buttons(self, enable=True):
        self.button_generate_master.Enable()
        self.button_generate_invoices.Enable()

    def on_generate_master(self, event=None):
        progress = wx.ProgressDialog("Generating Master PDF",
                                     "Please wait...\n\n"
                                     "Processing family:",
                                     parent=self,
                                     maximum=len(self.family_provider.get_families()),
                                     style=wx.PD_SMOOTH | wx.PD_APP_MODAL | wx.PD_ELAPSED_TIME | wx.PD_CAN_ABORT
                                     )
        # start_thread(self.generate_invoices, progress)
        progress.ShowModal()
        self.check_error()

    def on_generate_invoices(self, event=None):
        families = self.family_provider.get_families()
        progress = wx.ProgressDialog("Generating Invoices",
                                     "Please wait...\n\n"
                                     "Generating invoice for family:",
                                     maximum=len(families), parent=self,
                                     style=wx.PD_SMOOTH | wx.PD_APP_MODAL | wx.PD_ELAPSED_TIME | wx.PD_CAN_ABORT
                                     )
        class_map = self.fee_provider.generate_class_map()
        start_thread(generate_invoices, families, class_map, progress)
        progress.ShowModal()
        self.check_error()

    def check_error(self):
        if self.error_msg:
            caption = 'Error'
            dlg = wx.MessageDialog(self, self.error_msg,
                                   caption, wx.OK | wx.ICON_WARNING)
            self.error_msg = None
            dlg.ShowModal()
            dlg.Destroy()

    def get_data(self):
        return {}

    def load_data(self, data):
        self.modified = False
