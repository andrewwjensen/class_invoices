from enum import Enum


class Column(Enum):
    NONCONSECUTIVE = 'is_nonconsecutive'
    NEW_STUDENT = 'is_new_student'
    NOTES = 'notes'
    GRADE = 'grade'
    GENDER = 'gender'
    BIRTHDAY = 'birth_date'
    PHONE = 'phone'
    PARENT_TYPE = 'parent_type'
    EMAIL = 'email'
    MEMBER_TYPE = 'member_type'
    REGISTERED = 'registered_at'
    CLASSES = 'classes'
    FIRST_NAME = 'first_name'
    LAST_NAME = 'last_name'
    FAMILY_ID = 'family_id'
