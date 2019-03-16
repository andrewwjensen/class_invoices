import csv
import os
import traceback

import wx

from model.fee_schedule import read_fee_schedule
from ui.AutoWidthListCtrl import AutoWidthEditableListCtrl
from ui.ListSorterPanel import ListSorterPanel

DEFAULT_BORDER = 5


class FeeSchedulePanel(ListSorterPanel):

    def __init__(self, parent, border=DEFAULT_BORDER, *args, **kwargs):
        ListSorterPanel.__init__(self,
                                 parent=parent,
                                 my_id=wx.ID_ANY,
                                 listctl_class=AutoWidthEditableListCtrl,
                                 editable_columns=[1, 2],
                                 *args, **kwargs)
        self.button_import = wx.Button(self, wx.ID_ANY, "Import Fee Schedule...")
        self.button_export = wx.Button(self, wx.ID_ANY, "Export Fee Schedule...")
        self.parent = parent
        self.__do_layout(border)

    def __do_layout(self, border):
        sizer_fee_table = wx.BoxSizer(wx.VERTICAL)
        sizer_fee_buttons = wx.BoxSizer(wx.HORIZONTAL)

        self.SetMinSize((200, 100))
        sizer_fee_table.Add(self.GetListCtrl(), 1, wx.EXPAND | wx.ALL, border)

        sizer_fee_buttons.Add(self.button_import, 0, wx.EXPAND | wx.ALL, border)
        self.Bind(wx.EVT_BUTTON, self.on_import, self.button_import)
        sizer_fee_buttons.Add(self.button_export, 0, wx.EXPAND | wx.ALL, border)
        self.Bind(wx.EVT_BUTTON, self.on_export, self.button_export)
        sizer_fee_table.Add(sizer_fee_buttons, 0, wx.EXPAND | wx.ALL, border)

        self.SetSizer(sizer_fee_table)
        self.button_import.Disable()
        self.button_export.Disable()

    def on_import(self, event=None):
        dirname = ''
        file_dialog = wx.FileDialog(parent=self.parent,
                                    message="Choose a fee schedule CSV file",
                                    defaultDir=dirname,
                                    defaultFile="",
                                    wildcard="*.csv",
                                    style=wx.FD_OPEN)
        if file_dialog.ShowModal() == wx.ID_OK:
            filename = file_dialog.GetFilename()
            dirname = file_dialog.GetDirectory()
            try:
                fee_schedule_filename = os.path.join(dirname, filename)
                fee_schedule = read_fee_schedule(fee_schedule_filename)
                self.show_fee_schedule(fee_schedule)
            except Exception as e:
                self.parent.error_msg = "Error while reading fee schedule: " + str(e)
                traceback.print_exc()
        file_dialog.Destroy()
        self.check_error()

    def on_export(self, event=None):
        dirname = ''
        file_dialog = wx.FileDialog(parent=self.parent,
                                    message="Export fee schedule to CSV",
                                    defaultDir=dirname,
                                    defaultFile="",
                                    wildcard="*.csv",
                                    style=wx.FD_SAVE)
        if file_dialog.ShowModal() == wx.ID_OK:
            filename = file_dialog.GetFilename()
            dirname = file_dialog.GetDirectory()
            try:
                with open(os.path.join(dirname, filename), 'w') as f:
                    csv_writer = csv.writer(f)
                    for r in range(self.GetListCtrl().GetItemCount()):
                        row = [self.GetListCtrl().GetItem(r, c).GetText() for
                               c in range(self.GetListCtrl().GetColumnCount())]
                        csv_writer.writerow(row)
            except Exception as e:
                self.error_msg = "Error while exporting fee schedule: " + str(e)
                traceback.print_exc()
        file_dialog.Destroy()
        self.check_error()

    def show_fee_schedule(self, fee_schedule):
        # First, build a map of class name to row number on the displayed fee schedule
        class_to_row = {}
        for r in range(self.GetListCtrl().GetItemCount()):
            class_name = self.GetListCtrl().GetItem(r, 0).GetText()
            class_to_row[class_name] = r

        # Now open the fee schedule CSV and process its rows
        for fee_entry in fee_schedule:
            try:
                display_row_num = class_to_row[fee_entry[0]]
                self.set_item(display_row_num, 1, fee_entry[1])
                self.set_item(display_row_num, 2, fee_entry[2])
            except KeyError:
                # Ignore classes that are not needed for any registered student
                pass
        self.SetColumnCount(3)
        self.resize_column(1)
        self.resize_column(2)
        self.Refresh()

    def enable_buttons(self, enable=True):
        self.button_import.Enable(enable)
        self.button_export.Enable(enable)
