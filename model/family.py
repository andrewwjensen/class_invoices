import csv

from model.columns import Column
from model.parse import parse_bool, parse_list, parse_date

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
VALID_MEMBER_TYPES = ['parent', 'student']
VALID_PARENT_TYPES = ['mother', 'father']
VALID_GENDERS = ['male', 'female']


def get_parents(family):
    return family['parents']


def get_students(family):
    return family['students']


def transform(col_name, value, transforms):
    try:
        transform_func = transforms[col_name]
    except KeyError:
        return value
    return transform_func(value)


def parse_headers(row):
    validate_header_row(row)
    column_idx_to_name = {}
    for n, header in enumerate(row):
        column_idx_to_name[n] = Column(header)
    return column_idx_to_name


def validate_header_row(row):
    missing_columns = []
    for column in REQUIRED_COLUMNS:
        if column.value not in row:
            missing_columns.append(column.value)
    if missing_columns:
        raise RuntimeError('Missing required columns: ' + ', '.join(missing_columns))


def add_to_family(person, families):
    family_id = person[Column.FAMILY_ID]
    try:
        if person[Column.MEMBER_TYPE].lower() == 'parent':
            families[family_id]['parents'].append(person)
        else:
            families[family_id]['students'].append(person)
    except KeyError:
        families[family_id] = {
            'id': family_id,
            'last_name': person[Column.LAST_NAME],
            'parents': [],
            'students': [],
        }
        add_to_family(person, families)


def get_classes(families):
    classes = set()
    for family in families.values():
        for student in family['students']:
            classes = classes.union(student[Column.CLASSES])
    return classes


def load_families(path):
    first_row = True
    families = {}
    column_idx_to_name = None
    with open(path, 'r') as f:
        reader = csv.reader(f)
        for row in reader:
            if first_row:
                # This is the first row, process headers
                column_idx_to_name = parse_headers(row)
                first_row = False
            else:
                parse_person(row, column_idx_to_name, families)
    return families


def parse_person(row, column_idx_to_name, families):
    person = create_person(row, column_idx_to_name)
    add_to_family(person, families)


def create_person(row, column_idx_to_name):
    person = {}
    for n, column in enumerate(row):
        col_name = column_idx_to_name[n]
        person[col_name] = column
    for col_name, value in person.items():
        person[col_name] = transform(col_name, value, PARSE_TRANSFORMS)
    validate_person(person)
    return person


def validate_person(person):
    if person[Column.MEMBER_TYPE] and person[Column.MEMBER_TYPE] not in VALID_MEMBER_TYPES:
        raise RuntimeError("Invalid person: bad " + Column.MEMBER_TYPE.value +
                           " column. Got '" + person[Column.MEMBER_TYPE] +
                           "'. Valid member types: " + ', '.join(VALID_MEMBER_TYPES))
    elif person[Column.PARENT_TYPE] and person[Column.PARENT_TYPE] not in VALID_PARENT_TYPES:
        raise RuntimeError("Invalid person: bad " + Column.PARENT_TYPE.value +
                           " column. Got '" + person[Column.PARENT_TYPE] +
                           "'. Valid parent types: " + ', '.join(VALID_PARENT_TYPES))
    elif person[Column.GENDER] and person[Column.GENDER] not in VALID_GENDERS:
        raise RuntimeError("Invalid person: bad " + Column.GENDER.value +
                           " column. Got '" + person[Column.GENDER] +
                           "'. Valid parent types: " + ', '.join(VALID_GENDERS))
