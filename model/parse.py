import datetime
import re
from decimal import Decimal


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


def parse_phone(in_str):
    s = in_str.translate({ord(c): None for c in '()-.'})
    if len(s) > 4:
        s = s[:-4] + '-' + s[-4:]
    if len(s) > 8:
        s = s[:-8] + '-' + s[-8:]
    return s


def validate_currency(fee_str):
    if fee_str is not None:
        m = re.match(r'^ *\$? *(\d+(?:[.]\d{2})?) *$', fee_str)
        if m:
            return Decimal(m.group(1))
    return None
