import csv
import logging
from decimal import Decimal

from model.parse import validate_currency

logger = logging.getLogger(f'classinvoices.{__name__}')


def validate_fee_schedule_row(r, row, errors=None):
    if errors is None:
        errors = []
    if len(row) < 3:
        errors.append(f'Too few columns ({len(row)} < 3) in fee schedule on row {r + 1}: {row}')
        row.extend(['', '', ''])  # Make sure we have enough columns to process below
    class_name = row[0]
    fee = validate_currency(row[2])
    if fee is None:
        errors.append(f'Invalid currency in row {r + 1}, column 3 of fee schedule: {row[2]}')
        fee = Decimal(0.0)
    teacher = row[1]
    if not teacher and fee:
        raise RuntimeError(f'Empty teacher in row {r + 1}, column 2 of fee schedule when fee is not $0')
    return [class_name, teacher, fee]


def read_fee_schedule(path, errors=None):
    """Now open the fee schedule CSV and process its rows.
    Return a list of fee schedule rows, which are 3-tuples:
    (Class name (str), Teacher (str), Fee (Decimal, 2 places))"""
    if errors is None:
        errors = []
    fee_schedule = []
    with open(path, 'r') as f:
        reader = csv.reader(f)
        for r, row in enumerate(reader):
            try:
                fee_schedule.append(validate_fee_schedule_row(r, row, errors=errors))
            except KeyError:
                # Ignore validation error on first row, as it may be a header row
                if r != 0:
                    raise
    return fee_schedule
