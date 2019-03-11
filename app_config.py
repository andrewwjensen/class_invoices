# from PyQt5.QtCore import QSettings

PUBLISHER_Name = 'AndyJensen'
APP_NAME = 'ClassInvoices'

DEFAULT_DIRECTORY_KEY = 'default_dir'
RECENT_FILES_KEY = 'recent'
EMAIL_MESSAGE_KEY = 'email_body'
EMAIL_SUBJECT_KEY = 'email_subject'

DEFAULTS = {
    RECENT_FILES_KEY: [],
    DEFAULT_DIRECTORY_KEY: '',
    EMAIL_MESSAGE_KEY: 'Attached, please find the class enrollment invoice for your student\'s classes this semester.',
    EMAIL_SUBJECT_KEY: 'Enrollment Invoice 2019, Semester 2',
}

conf = None


class MockSettings(object):
    def __init__(self):
        self.settings = {}

    def setValue(self, k, v):
        self.settings[k] = v

    def value(self, k):
        try:
            return self.settings[k]
        except KeyError:
            return None


class Config(object):
    def __init__(self, publisher, application):
        self.publisher = publisher
        self.application = application
        # self.settings = QSettings(self.publisher, self.application)
        self.settings = MockSettings()
        self.create_config()

    def create_config(self):
        for k, v in DEFAULTS.items():
            if self.get(k) is None:
                self.settings.setValue(k, v)
        self.save_config()

    def save_config(self):
        # This will write the setting to the platform specific storage.
        # del self.settings
        # self.settings = QSettings(self.publisher, self.application)
        pass

    def set(self, key, value):
        self.settings.setValue(key, value)
        self.save_config()

    def get(self, key):
        value = self.settings.value(key)
        return value


if conf is None:
    conf = Config(PUBLISHER_Name, APP_NAME)
