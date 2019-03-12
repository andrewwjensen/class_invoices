from model.columns import Column
import model.parse

VALID_MEMBER_TYPES = ['parent', 'student']
VALID_PARENT_TYPES = ['mother', 'father']
VALID_GENDERS = ['male', 'female']


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


def create_person(row, column_idx_to_name):
    person = {}
    for n, column in enumerate(row):
        col_name = column_idx_to_name[n]
        person[col_name] = column
    for col_name, value in person.items():
        person[col_name] = model.parse.transform(col_name, value, model.parse.PARSE_TRANSFORMS)
    validate_person(person)
    return person
