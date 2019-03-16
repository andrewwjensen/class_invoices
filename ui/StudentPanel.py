from ui.ListSorterPanel import ListSorterPanel


class StudentPanel(ListSorterPanel):
    def __init__(self, parent, my_id, *args, **kwargs):
        super().__init__(parent, my_id, *args, **kwargs)
        self.SetMinSize((400, 100))


def show_headers(self):
    display_row = []
    for header in REQUIRED_COLUMNS:
        display_header = COLUMN_DISPLAY_MAP[header]
        self.student_panel.add_column(display_header)
        display_row.append(display_header)
    # Update ColumnSorterMixin column count
    self.student_panel.SetColumnCount(len(REQUIRED_COLUMNS))


def show_families(self, families):
    self.student_panel.SortListItems(1)

    self.show_classes()


def show_students(students):
    for student in students:
        for class_name in student[Column.CLASSES]:
            self.classes.add(class_name)
        for c, column in enumerate(REQUIRED_COLUMNS):
            col_value = transform(column, student[column], DISPLAY_TRANSFORMS)
            if c == 0:
                self.student_panel.insert_item(row_num, col_value)
            else:
                self.student_panel.set_item(row_num, c, col_value)
            self.student_panel.resize_column(c)
        row_num += 1
    return row_num
