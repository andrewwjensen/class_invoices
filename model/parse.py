import datetime
import re
from decimal import Decimal

import model.family
import model.person
from model.columns import Column

REQUIRED_COLUMNS = [
    Column.FAMILY_ID,
    Column.LAST_NAME,
    Column.FIRST_NAME,
    Column.CLASSES,
]

PARSE_TRANSFORMS = {
    Column.NEW_STUDENT: lambda value: parse_bool(value),
    Column.NONCONSECUTIVE: lambda value: parse_bool(value),
    Column.CLASSES: lambda value: parse_list(value),
    Column.REGISTERED: lambda value: parse_date(value),
    Column.BIRTHDAY: lambda value: parse_date(value),
}


def parse_bool(bool_str):
    if bool_str is None:
        return False
    val = bool_str.strip().lower()
    return val not in ['', 'no', 'n', 'false', 'f', '0']


def parse_date(date_str):
    try:
        return datetime.datetime.strptime(date_str, '%m/%d/%Y %H:%M')
    except ValueError:
        return date_str


def parse_list(list_str):
    """Parse comma-separated list"""
    if list_str.strip():
        return [t.strip() for t in list_str.split(',') if t.strip()]
    else:
        return []


def parse_headers(row):
    validate_header_row(row)
    column_idx_to_name = {}
    for n, header in enumerate(row):
        column_idx_to_name[n] = Column(header)
    return column_idx_to_name


def parse_person(row, column_idx_to_name, families):
    person = model.person.create_person(row, column_idx_to_name)
    model.family.add_to_family(person, families)


def transform(col_name, value, transforms):
    try:
        transform_func = transforms[col_name]
    except KeyError:
        return value
    return transform_func(value)


def validate_header_row(row):
    missing_columns = []
    for column in REQUIRED_COLUMNS:
        if column.value not in row:
            missing_columns.append(column.value)
    if missing_columns:
        raise RuntimeError('Missing required columns: ' + ', '.join(missing_columns))


def validate_currency(fee_str):
    if fee_str is not None:
        m = re.match(r'^ *\$? *(\d+(?:[.]\d{2})?) *$', fee_str)
        if m:
            return Decimal(m.group(1))
    return None
