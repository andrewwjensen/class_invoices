from model.columns import Column


def get_parents(family):
    return family['parents']


def get_students(family):
    return family['students']


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
