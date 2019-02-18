from PyQt5.QtCore import QSettings

RECENT_FILES_KEY = 'recent'


class Config(object):
    def __init__(self, publisher, application):
        self.publisher = publisher
        self.application = application
        self.settings = QSettings(self.publisher, self.application)
        # self.create_config()

    def create_config(self):
        self.settings.setValue(RECENT_FILES_KEY, ["file1", "file2"])
        self.save_config()

    def save_config(self):
        # This will write the setting to the platform specific storage.
        del self.settings
        self.settings = QSettings(self.publisher, self.application)

    def get_config(self, key, typ):
        print("andy value = " + str(self.settings.value(key, typ)))

    def set_config(self, key, value):
        self.settings.setValue(key, value)
        self.save_config()
