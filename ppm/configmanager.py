import ConfigParser
from utility import *
import os

# config base directory
CONFIG_DIRECTORY_LOCATION = joinPaths(os.environ["HOME"] if "HOME" in os.environ else "~",".pdm")

# config file relative path
CONFIG_FILE = ".config"

class ConfigManager:
    def __init__(self):
    	new_directory(CONFIG_DIRECTORY_LOCATION)
    	configFilePath = joinPaths(CONFIG_DIRECTORY_LOCATION,CONFIG_FILE)
    	config = ConfigParser.RawConfigParser()
        if os.path.exists(configFilePath):
            config.read(configFilePath)
        self.config = config

    def get_deps_map_location(self):
    	if self.config.has_option("depstourlmap","location"):
    		return self.config.get("depstourlmap","location")

    def set_deps_map_location(self, location):
    	assert(location)
    	if not self.config.has_section("depstourlmap"):
    		self.config.add_section("depstourlmap")
    	self.config.set("depstourlmap", "location", location)

    def save(self):
    	configFilePath = joinPaths(CONFIG_DIRECTORY_LOCATION,CONFIG_FILE)
    	if not os.path.exists(configFilePath):
			with open(configFilePath, 'w+') as configfile:
				self.config.write(configfile)
