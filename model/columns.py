from enum import Enum


class Column(Enum):
    FAMILY_ID = 'family_id'
    LAST_NAME = 'last_name'
    FIRST_NAME = 'first_name'
    CLASSES = 'classes'
    REGISTERED = 'registered_at'
    MEMBER_TYPE = 'member_type'
    EMAIL = 'email'
    PARENT_TYPE = 'parent_type'
    PHONE = 'phone'
    BIRTHDAY = 'birth_date'
    GENDER = 'gender'
    GRADE = 'grade'
    NOTES = 'notes'
    NEW_STUDENT = 'is_new_student'
    NONCONSECUTIVE = 'is_nonconsecutive'
