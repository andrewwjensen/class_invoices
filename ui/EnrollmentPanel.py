import logging
import os
import tempfile

import wx
import wx.lib.newevent

from model.family import load_families, export_families
from ui.EmailSetupPanel import EmailSetupPanel
from ui.FamilyListFrame import FamilyListFrame
from ui.PdfPanel import PdfPanel

DEFAULT_BORDER = 5

logger = logging.getLogger(f'classinvoices.{__name__}')


class EnrollmentPanel(wx.Panel):
    EnrollmentDataEvent, EVT_ENROLLMENT_DATA_CHANGED = wx.lib.newevent.NewEvent()

    def __init__(self, border=DEFAULT_BORDER, *args, **kwargs):
        wx.Panel.__init__(self, *args, **kwargs)

        self.tempdir = tempfile.TemporaryDirectory()
        logger.debug(f'tempdir: {self.tempdir}')

        self.button_load_enrollment = wx.Button(self, wx.ID_ANY, 'Load Enrollment List...')
        self.button_export_enrollment = wx.Button(self, wx.ID_ANY, 'Export Enrollment List...')
        self.button_show_students = wx.Button(self, wx.ID_ANY, 'Preview Enrollment List...')

        # Notebook (tabbed pane with PDF and Email tabs)
        self.action_tabs = wx.Notebook(self, wx.ID_ANY)
        self.pdf_tab_panel = PdfPanel(self.tempdir.name,
                                      parent=self.action_tabs,
                                      id=wx.ID_ANY,
                                      border=border)
        self.email_tab_panel = EmailSetupPanel(parent=self.action_tabs,
                                               id=wx.ID_ANY,
                                               border=border)

        # We are the family provider
        self.pdf_tab_panel.set_family_provider(self)
        self.pdf_tab_panel.set_email_provider(self.email_tab_panel)

        self.__do_layout(border)
        self.SetMinSize((500, 400))

        self.families = {}
        self.class_map = {}
        self.modified = False
        self.error_msg = None
        self.sub_windows = set()

    def __do_layout(self, border):
        sizer_enrollment_panel = wx.BoxSizer(wx.VERTICAL)
        sizer_enrollment_upper = wx.BoxSizer(wx.VERTICAL)
        sizer_buttons = wx.BoxSizer(wx.HORIZONTAL)
        sizer_stats = wx.BoxSizer(wx.HORIZONTAL)

        # Enrollment part, top of panel, above pdf/email notebook (tabbed panels)
        sizer_buttons.Add(self.button_load_enrollment, 0, wx.ALL, border)
        self.button_load_enrollment.Bind(wx.EVT_BUTTON, self.on_load)
        sizer_buttons.Add(self.button_export_enrollment, 0, wx.ALL, border)
        self.button_export_enrollment.Bind(wx.EVT_BUTTON, self.on_export)
        sizer_buttons.Add(self.button_show_students, 0, wx.ALL, border)
        self.button_show_students.Bind(wx.EVT_BUTTON, self.show_students)
        sizer_enrollment_upper.Add(sizer_buttons)

        # Stats
        label_families = wx.StaticText(self, wx.ID_ANY, 'Families:')
        sizer_stats.Add(label_families, 0, wx.LEFT | wx.TOP | wx.BOTTOM, border)
        self.label_num_families = wx.StaticText(self, wx.ID_ANY, '0')
        sizer_stats.Add(self.label_num_families, 0, wx.RIGHT | wx.TOP | wx.BOTTOM, border)
        label_parents = wx.StaticText(self, wx.ID_ANY, 'Parents:')
        sizer_stats.Add(label_parents, 0, wx.LEFT | wx.TOP | wx.BOTTOM, border)
        self.label_num_parents = wx.StaticText(self, wx.ID_ANY, '0')
        sizer_stats.Add(self.label_num_parents, 0, wx.RIGHT | wx.TOP | wx.BOTTOM, border)
        label_students = wx.StaticText(self, wx.ID_ANY, 'Students:')
        sizer_stats.Add(label_students, 0, wx.LEFT | wx.TOP | wx.BOTTOM, border)
        self.label_num_students = wx.StaticText(self, wx.ID_ANY, '0')
        sizer_stats.Add(self.label_num_students, 0, wx.RIGHT | wx.TOP | wx.BOTTOM, border)
        sizer_enrollment_upper.Add(sizer_stats, 1, wx.EXPAND, border)
        sizer_enrollment_panel.Add(sizer_enrollment_upper, 0, wx.EXPAND | wx.ALL, border)

        # Disable all buttons except Load
        self.button_show_students.Disable()

        # Pull it all together into the main sizer
        self.action_tabs.AddPage(self.pdf_tab_panel, self.pdf_tab_panel.get_name())
        self.action_tabs.AddPage(self.email_tab_panel, self.email_tab_panel.get_name())
        sizer_enrollment_panel.Add(self.action_tabs, 1, wx.EXPAND | wx.ALL, border)
        self.SetSizer(sizer_enrollment_panel)

    def close(self):
        self.pdf_tab_panel.close()

    def is_modified(self):
        return self.modified or self.email_tab_panel.is_modified() or self.pdf_tab_panel.is_modified()

    def clear_is_modified(self):
        self.modified = False
        self.email_tab_panel.clear_is_modified()
        self.pdf_tab_panel.clear_is_modified()

    def set_fee_provider(self, provider):
        self.pdf_tab_panel.set_fee_provider(provider)

    def get_families(self):
        return self.families

    def on_load(self, _event=None):
        """Load a new class enrollment CSV file."""
        dirname = ''
        file_dialog = wx.FileDialog(parent=None,
                                    message='Choose an enrollment CSV file',
                                    defaultDir=dirname,
                                    defaultFile='',
                                    wildcard='*.csv',
                                    style=wx.FD_OPEN)
        if file_dialog.ShowModal() == wx.ID_OK:
            filename = file_dialog.GetFilename()
            dirname = file_dialog.GetDirectory()
            path = os.path.join(dirname, filename)
            try:
                self.load_enrollment_data(path)
                self.pdf_tab_panel.populate_family_list()
                self.modified = True
            except Exception as e:
                self.error_msg = f'Error while loading enrollment file: {e}'
                logger.exception(self.error_msg)
        file_dialog.Destroy()
        self.check_error()

    def get_export_path(self):
        path = None
        suffix = '.csv'
        file_dialog = wx.FileDialog(parent=self,
                                    message='Export enrollment list to CSV',
                                    defaultDir='',
                                    defaultFile='Enrollment List (Exported).csv',
                                    wildcard=f'*{suffix}',
                                    style=wx.FD_SAVE)
        if file_dialog.ShowModal() == wx.ID_OK:
            path = file_dialog.GetPath()
            if not path.endswith(suffix):
                path += suffix
        file_dialog.Destroy()
        return path

    def on_export(self, _event=None):
        """Export the class enrollment to a CSV file."""
        try:
            path = self.get_export_path()
            if path:
                self.export_enrollment_data(path)
        except Exception as e:
            self.error_msg = f'Error while loading enrollment file: {e}'
            logger.exception(self.error_msg)
        self.check_error()

    def load_enrollment_data(self, path):
        self.families = load_families(path)
        self.refresh()

    def export_enrollment_data(self, path):
        try:
            export_families(path, self.families)
        except Exception as e:
            self.error_msg = f'Error while loading enrollment file: {e}'
            logger.exception(self.error_msg)

    def refresh(self):
        self.set_stats()
        event = self.EnrollmentDataEvent()
        wx.PostEvent(self.GetEventHandler(), event)

    def set_stats(self):
        num_families = len(self.families)
        num_parents = 0
        num_students = 0
        for family in self.families.values():
            num_parents += len(family['parents'])
            num_students += len(family['students'])
        self.label_num_families.SetLabelText(str(num_families))
        self.label_num_parents.SetLabelText(str(num_parents))
        self.label_num_students.SetLabelText(str(num_students))
        # Force the panel to redo its layout since widths may have changed:
        self.Layout()

    def enable_buttons(self, enable=True):
        self.button_show_students.Enable(enable)
        self.pdf_tab_panel.enable_buttons(enable)
        self.email_tab_panel.enable_buttons(enable)

    def show_students(self, _event=None):
        family_frame = FamilyListFrame(parent=self)
        family_frame.set_families(self.families)
        self.sub_windows.add(family_frame)
        family_frame.Show()
        family_frame.Bind(wx.EVT_CLOSE, self.on_close_sub_window)

    def on_close_sub_window(self, event=None):
        self.sub_windows.remove(event.GetEventObject())
        event.Skip()

    def close_sub_window(self):
        for window in self.sub_windows:
            if window.IsActive():
                window.Close()
                break
        else:
            self.pdf_tab_panel.close_sub_window()

    def check_error(self):
        if self.error_msg:
            caption = 'Error'
            dlg = wx.MessageDialog(parent=None,
                                   message=self.error_msg,
                                   caption=caption,
                                   style=wx.OK | wx.ICON_WARNING)
            self.error_msg = None
            dlg.ShowModal()
            dlg.Destroy()

    def get_data(self):
        return {
            'families': self.families,
            'pdf_tab': self.pdf_tab_panel.get_data(),
            'email_tab': self.email_tab_panel.get_data(),
            'selected_tab': self.action_tabs.GetSelection(),
        }

    def load_data(self, data):
        if 'families' in data:
            self.families = data['families']
        else:
            self.families = {}
        self.refresh()
        if 'pdf_tab' in data:
            self.pdf_tab_panel.load_data(data['pdf_tab'])
        else:
            self.pdf_tab_panel.load_data({})
        if 'email_tab' in data:
            self.email_tab_panel.load_data(data['email_tab'])
        else:
            self.email_tab_panel.load_data({})
        if 'selected_tab' in data:
            self.action_tabs.SetSelection(data['selected_tab'])
        else:
            self.action_tabs.SetSelection(0)
