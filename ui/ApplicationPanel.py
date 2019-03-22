import logging

import wx

import app_config
from model.columns import Column
from ui.EnrollmentPanel import EnrollmentPanel
from ui.FeeSchedulePanel import FeeSchedulePanel

BORDER_WIDTH = 5

DISPLAY_TRANSFORMS = {
    Column.CLASSES: lambda value: ', '.join(value),
}

COLUMN_DISPLAY_MAP = {
    Column.FAMILY_ID: 'Family ID',
    Column.REGISTERED: 'Register Date',
    Column.MEMBER_TYPE: 'Parent/Student',
    Column.LAST_NAME: 'Last Name',
    Column.FIRST_NAME: 'First Name',
    Column.EMAIL: 'E-mail Address',
    Column.PARENT_TYPE: 'Mother/Father',
    Column.PHONE: 'Phone',
    Column.BIRTHDAY: 'Birthday',
    Column.GENDER: 'Gender',
    Column.GRADE: 'Grade',
    Column.NOTES: 'Notes',
    Column.NEW_STUDENT: 'New?',
    Column.NONCONSECUTIVE: 'Nonconsecutive?',
    Column.CLASSES: 'Classes',
}

logging.basicConfig()
logger = logging.getLogger(app_config.APP_NAME)
logger.setLevel(logging.INFO)


class ApplicationPanel(wx.Panel):
    """This Panel holds the main application data, a table of CSV values."""

    def __init__(self, *args, **kwargs):
        wx.Panel.__init__(self, *args, **kwargs)

        self.splitter = wx.SplitterWindow(self, wx.ID_ANY)
        self.enrollment_panel = EnrollmentPanel(parent=self.splitter,
                                                id=wx.ID_ANY,
                                                border=BORDER_WIDTH)
        self.fee_schedule_panel = FeeSchedulePanel(parent=self.splitter,
                                                   id=wx.ID_ANY,
                                                   border=BORDER_WIDTH)
        self.enrollment_panel.set_fee_provider(self.fee_schedule_panel)

        self.__set_properties()
        self.__do_layout()

        self.Bind(wx.EVT_SIZE, self.on_resize)
        self.Bind(wx.EVT_SPLITTER_SASH_POS_CHANGED, self.on_sash_changed)
        self.enrollment_panel.Bind(EnrollmentPanel.EVT_ENROLLMENT_DATA_CHANGED, self.on_enrollment_change)

        self.sash_proportion = 0.5
        self.error_msg = None

    def __set_properties(self):
        # begin wxGlade: MyFrame.__set_properties
        self.splitter.SetMinimumPaneSize(500)
        # end wxGlade

    def __do_layout(self):
        # begin wxGlade: MyFrame.__do_layout
        sizer_window = wx.BoxSizer(wx.VERTICAL)

        self.splitter.SplitVertically(self.enrollment_panel, self.fee_schedule_panel)
        sizer_window.Add(self.splitter, 1, wx.EXPAND | wx.ALL, BORDER_WIDTH)
        self.SetSizer(sizer_window)
        self.SetAutoLayout(True)
        self.Layout()
        # end wxGlade

    def close(self):
        self.enrollment_panel.close()

    def is_modified(self):
        return self.enrollment_panel.is_modified() or self.fee_schedule_panel.is_modified()

    def clear_is_modified(self):
        self.enrollment_panel.clear_is_modified()
        self.fee_schedule_panel.clear_is_modified()

    def on_resize(self, event=None):
        """Window has been resized, so we need to adjust the sash based on self.proportion."""
        self.splitter.SetSashPosition(self.get_expected_sash_position())
        if event is not None:
            event.Skip()

    def on_sash_changed(self, event=None):
        width = max(self.splitter.GetMinimumPaneSize(), self.GetParent().GetClientSize().width)
        self.sash_proportion = self.splitter.GetSashPosition() / width

    def get_expected_sash_position(self):
        width = max(self.splitter.GetMinimumPaneSize(), self.GetParent().GetClientSize().width)
        return int(round(width * self.sash_proportion))

    def on_enrollment_change(self, event=None):
        self.fee_schedule_panel.populate_fee_schedule(self.enrollment_panel.get_families())
        self.enable_buttons()

    def enable_buttons(self):
        self.enrollment_panel.enable_buttons()
        self.fee_schedule_panel.enable_buttons()

    def get_data(self):
        return {
            'sash_proportion': self.sash_proportion,
            'enrollment': self.enrollment_panel.get_data(),
            'fee_schedule': self.fee_schedule_panel.get_data(),
        }

    def load_data(self, data):
        if 'sash_proportion' in data:
            self.sash_proportion = data['sash_proportion']
            self.on_resize()
        else:
            logger.debug('no sash proportion')
        self.enrollment_panel.load_data(data['enrollment'])
        self.fee_schedule_panel.load_data(data['fee_schedule'])
        self.Refresh()
