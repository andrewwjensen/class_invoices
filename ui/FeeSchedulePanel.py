import csv
import os
import traceback
from decimal import Decimal

import wx
import wx.lib.newevent

from model.family import get_classes
from model.fee_schedule import read_fee_schedule
from ui.ListSorterPanel import ListSorterPanel

DEFAULT_BORDER = 5


class FeeSchedulePanel(ListSorterPanel):
    ImportFeeScheduleEvent, EVT_FEE_SCHEDULE_IMPORTED = wx.lib.newevent.NewEvent()

    def __init__(self, parent, border=DEFAULT_BORDER, *args, **kwargs):
        ListSorterPanel.__init__(self,
                                 parent=parent,
                                 my_id=wx.ID_ANY,
                                 editable_columns=[1, 2],
                                 *args, **kwargs)
        self.button_import = wx.Button(self, wx.ID_ANY, "Import Fee Schedule...")
        self.button_export = wx.Button(self, wx.ID_ANY, "Export Fee Schedule...")
        self.__do_layout(border)
        self.error_msg = None

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

    def is_modified(self):
        return self.list_ctrl.is_modified()

    def on_import(self, event=None):
        dirname = ''
        file_dialog = wx.FileDialog(parent=self,
                                    message="Choose a fee schedule CSV file",
                                    defaultDir=dirname,
                                    defaultFile="",
                                    wildcard="*.csv",
                                    style=wx.FD_OPEN)
        if file_dialog.ShowModal() == wx.ID_OK:
            filename = file_dialog.GetFilename()
            dirname = file_dialog.GetDirectory()
            try:
                fee_schedule_path = os.path.join(dirname, filename)
                self.load_fee_schedule(fee_schedule_path)
                self.modified = True
            except Exception as e:
                self.error_msg = "Error while reading fee schedule: " + str(e)
                traceback.print_exc()
        file_dialog.Destroy()
        self.check_error()

    def on_export(self, event=None):
        dirname = ''
        file_dialog = wx.FileDialog(parent=self,
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

    def load_fee_schedule(self, path):
        fee_schedule = read_fee_schedule(path)
        self.show_fee_schedule(fee_schedule)
        event = self.ImportFeeScheduleEvent()
        wx.PostEvent(self.GetEventHandler(), event)

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

    def populate_fee_schedule(self, families):
        self.add_column('Class')
        self.add_column('Teacher')
        self.add_column('Fee')

        for class_name in get_classes(families):
            self.add_row([class_name, '', ''], dedup_col=0)

        self.resize_column(0)
        self.SortListItems(0)

    def get_class_map(self):
        class_map = {}
        missing_classes = []
        for r in range(self.GetListCtrl().GetItemCount()):
            class_name = self.GetListCtrl().GetItem(r, 0).GetText()
            teacher = self.GetListCtrl().GetItem(r, 1).GetText()
            fee = self.GetListCtrl().GetItem(r, 2).GetText()
            if not teacher or not fee:
                missing_classes.append(class_name)
            else:
                class_map[class_name] = (teacher, Decimal(fee))
        if missing_classes:
            msg = 'Classes have missing teacher or fee:\n  ' + '\n  '.join(missing_classes)
            raise RuntimeError(msg)
        return class_map

    def check_error(self):
        if self.error_msg:
            caption = 'Error'
            dlg = wx.MessageDialog(self, self.error_msg,
                                   caption, wx.OK | wx.ICON_WARNING)
            self.error_msg = None
            dlg.ShowModal()
            dlg.Destroy()
