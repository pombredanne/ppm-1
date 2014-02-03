import ConfigParser
import utility
import os
from config import SETTINGS_DIR_PATH, SETTINGS_FILE_PATH

# setting names
GENERAL_SECTION = "general"
REGISTRY_SERVER_ADRESS = "registry-server-adress"
REPOSITORY_SERVER_ADRESS = "repository-server-adress"
CURRENT_PROJECT = "current-project"

class Settings:
    def __init__(self):
        utility.ensure_directory(SETTINGS_DIR_PATH)
        utility.ensure_file_directory(SETTINGS_FILE_PATH)

        settings = ConfigParser.RawConfigParser()
        if os.path.exists(SETTINGS_FILE_PATH):
            settings.read(SETTINGS_FILE_PATH)
        self.settings = settings
        if not self.settings.has_section(GENERAL_SECTION):
            self.settings.add_section(GENERAL_SECTION)

    def get_registry_server(self):
        return self.get_setting(REGISTRY_SERVER_ADRESS)

    def get_repository_server(self):
        return self.get_setting(REPOSITORY_SERVER_ADRESS)

    def get_current_project(self):
        return self.get_setting(CURRENT_PROJECT)


    def set_registry_server(self, adress):
        self.set_setting(REGISTRY_SERVER_ADRESS, adress)

    def set_repository_server(self, adress):
        self.set_setting(REPOSITORY_SERVER_ADRESS, adress)

    def set_current_project(self, project_name):
        self.set_setting(CURRENT_PROJECT, project_name)


    def set_setting(self, name, value):
        assert name
        if value != None:
            self.settings.set(GENERAL_SECTION, name, value)
        elif self.settings.has_option(GENERAL_SECTION, name):
            self.settings.remove_option(GENERAL_SECTION, name)

    def get_setting(self, name):
        assert name
        if self.settings.has_option(GENERAL_SECTION, name):
            return self.settings.get(GENERAL_SECTION, name)

    def save(self):
        with open(SETTINGS_FILE_PATH, 'w+') as settingsfile:
            self.settings.write(settingsfile)
