import ConfigParser
import utility
import os
from config import SETTINGS_DIR_PATH, SETTINGS_FILE_PATH


class Settings:
    def __init__(self):
        utility.ensure_directory(SETTINGS_DIR_PATH)
        utility.ensure_file_directory(SETTINGS_FILE_PATH)

        settings = ConfigParser.RawConfigParser()
        if os.path.exists(SETTINGS_FILE_PATH):
            settings.read(SETTINGS_FILE_PATH)
        self.settings = settings

    def get_registry_server(self):
        if self.settings.has_option("registry", "adress"):
            return self.settings.get("registry", "adress")

    def set_registry_server(self, adress):
        assert(adress)
        if not self.settings.has_section("registry"):
            self.settings.add_section("registry")
        self.settings.set("registry", "adress", adress)

    def get_mirror_server(self):
        if self.settings.has_option("mirror", "adress"):
            return self.settings.get("mirror", "adress")

    def set_mirror_server(self, adress):
        assert(adress)
        if not self.settings.has_section("mirror"):
            self.settings.add_section("mirror")
        self.settings.set("mirror", "adress", adress)

    def save(self):
        with open(SETTINGS_FILE_PATH, 'w+') as settingsfile:
            self.settings.write(settingsfile)
