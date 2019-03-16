import csv

from model.parse import validate_currency


def validate_fee_schedule_row(r, row):
    if len(row) < 3:
        raise RuntimeError(f'Too few columns in fee schedule on row {r + 1}: {row}')
    if not row[1]:
        raise RuntimeError(f'Empty teacher in row {r + 1}, column 2 of fee schedule')
    if not validate_currency(row[2]):
        raise RuntimeError(f'Invalid currency in row {r + 1}, column 3 of fee schedule: {row[2]}')
    return [row[0], row[1], validate_currency(row[2])]


def read_fee_schedule(path):
    """Now open the fee schedule CSV and process its rows.
    Return a list of fee schedule rows, which are 3-tuples:
    (Class name (str), Teacher (str), Fee (Decimal, 2 places))"""
    fee_schedule = []
    with open(path, 'r') as f:
        reader = csv.reader(f)
        r = 0
        for row in reader:
            try:
                fee_schedule.append(validate_fee_schedule_row(r, row))
            except RuntimeError:
                # Ignore validation error on first row, as it may be a header row
                if r != 0:
                    raise
            r += 1
    return fee_schedule
