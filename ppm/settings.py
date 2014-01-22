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

    def get_deps_map_location(self):
        if self.settings.has_option("mirror", "location"):
            return self.settings.get("mirror", "location")

    def set_deps_map_location(self, location):
        assert(location)
        if not self.settings.has_section("mirror"):
            self.settings.add_section("mirror")
        self.settings.set("mirror", "location", location)

    def save(self):
        with open(SETTINGS_FILE_PATH, 'w+') as settingsfile:
            self.settings.write(settingsfile)
