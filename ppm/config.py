import os
from utility import joinPaths


# Base Path
BASE_PATH = os.getcwd()

# JSON file specifying dependencies to install
REQDEPS_FILE_PATH = joinPaths(BASE_PATH, "dependencies.json")

# Directory that will contains downloaded dependencies
DEPSINSTALL_DIR_PATH = joinPaths(BASE_PATH, "dependencies/")

# Installed dependencies will be added to this file, this file is used to compare currently installed versions and required versions in order to determine which packages to install
CURRENTDEPS_FILE_PATH = joinPaths(DEPSINSTALL_DIR_PATH, "current_dependencies.json")

# Dependency manager config
TMPDOWNLOAD_DIR_REL_PATH =  "tmp/"
TMPEXTRACTION_DIR_REL_PATH = joinPaths(TMPDOWNLOAD_DIR_REL_PATH, "tmp/")

# Settings configuration

# Settings base directory absolute path
SETTINGS_DIR_PATH = joinPaths(os.environ["HOME"] if "HOME" in os.environ else "~", ".ppm/")
# Settings file absolute path
SETTINGS_FILE_PATH = joinPaths(SETTINGS_DIR_PATH, ".config")

# Generated environment file path
GENERATED_ENVIRONMENT_PATH = joinPaths(BASE_PATH, "depsenv.sh")

# Request Timeout in seconds
REQUEST_TIMEOUT = 5