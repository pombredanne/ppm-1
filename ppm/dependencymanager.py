import os
import shutil
import utility
from config import TMPDOWNLOAD_DIR_NAME, TMPEXTRACTION_DIR_NAME


class DependencyManager:
    def __init__(self, installed_dependencies, base_directory):
        assert (isinstance(installed_dependencies, InstalledDependencies))
        assert (base_directory and os.path.isdir(base_directory))

        self.dependencies_directory = base_directory
        self.download_directory = utility.joinPaths(base_directory, TMPDOWNLOAD_DIR_NAME)
        self.extraction_directory = utility.joinPaths(self.download_directory, TMPEXTRACTION_DIR_NAME)

        utility.remove_file_or_dir(self.extraction_directory)
        utility.remove_file_or_dir(self.download_directory)
        utility.ensure_directory(self.download_directory)
        utility.ensure_directory(self.extraction_directory)

        self.installedDependencies = installed_dependencies

    def install_dependency(self, dependencyName, version, url, installDirectoryRelPath):
        savePath = utility.download_file(url, self.download_directory)
        utility.clear_directory_contents(self.extraction_directory)

        utility.extract_file(savePath, self.extraction_directory)
        os.remove(savePath)

        if self.installedDependencies.is_installed(dependencyName):
            self.remove_dependency(dependencyName)

        # not sure wether to add this or not (can cause serious impact)
        #if os.path.exists(installDirectory):
        #    utility.log("installation directory {i} for dependency {d} already exist, overwriting it...".format(i=installDirectory,d=dependencyName))
        #    shutil.rmtree(installDirectory)

        installDirectory = utility.joinPaths(self.dependencies_directory, installDirectoryRelPath)        
        utility.ensure_directory(installDirectory)

        # if the archive top level contains only one directory,copy its contents(not the directory itself)
        tempDirContents = [name for name in os.listdir(self.extraction_directory)]
        if len(tempDirContents) == 1 and os.path.isdir(utility.joinPaths(self.extraction_directory, tempDirContents[0])):
            dirPath = utility.joinPaths(self.extraction_directory, tempDirContents[0])
            utility.move_directory_contents(dirPath, installDirectory)
            os.rmdir(dirPath)
        else:
            utility.move_directory_contents(self.extraction_directory, installDirectory)

        self.installedDependencies.add_dependency(dependencyName, version, installDirectoryRelPath)
        return True

    def remove_dependency(self, dependencyName):
        installRelPath = self.installedDependencies.get_installation_path(dependencyName)
        installLocation = utility.joinPaths(self.dependencies_directory, installRelPath)
        if os.path.exists(installLocation):
            try:
                shutil.rmtree(installLocation)
            except Exception:
                raise Exception("Error, can't remove {s}, ensure that you have prermissions and the program is not already running".format(s=installLocation))
        else:
            utility.log("directory {s} does not exist, this should happen only if you have deleted the directory manually, please report the problem otherwise".format(s=installLocation))
        self.installedDependencies.remove_dependency(dependencyName)

    def __del__(self):
        utility.remove_file_or_dir(self.download_directory)
        utility.remove_file_or_dir(self.extraction_directory)


class InstalledDependencies:
    def __init__(self, data):
        if data is None:
            self.data = {}
        elif self.__validate_schema(data):
            self.data = data
        else:
            raise ValueError("invalid Data")

    def get_dependencies_list(self):
        return dict([(k, v["version"]) for k,v in self.data.items()])

    def get_installed_version(self, depName):
        assert(self.is_installed(depName))
        return self.data[depName]["version"]

    def get_installation_path(self, depName):
        assert(self.is_installed(depName))
        return self.data[depName]["path"]

    def remove_dependency(self, dependencyName):
        assert (self.is_installed(dependencyName))
        del self.data[dependencyName]

    def add_dependency(self, depName, version, installationPath):
        assert (version and installationPath)
        assert (not self.is_installed(depName))
        self.data[depName] = {"version": version, "path": installationPath}

    def is_installed(self, depName, version=None):
        assert(depName)
        if depName in self.data and (version is None or version == self.data[depName]["version"]):
            return True
        else:
            return False

    # used for saving purpose
    def get_data(self):
        # return a copy of data to avoid external modification
        return dict(self.data)

    def __validate_schema(self, data):
        # TODO
        return True
