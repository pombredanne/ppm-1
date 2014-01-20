import os
import shutil
from utility import *

# temporary folder to extract compressed files in
TMP_EXTRACTION_DIRECTORY_NAME = "tmp"

class DependencyManager:
    def __init__(self, installedDependencies, downloadDirectory):
        assert (isinstance(installedDependencies,InstalledDependencies))
        assert downloadDirectory and os.path.exists(downloadDirectory)

        self.installedDependencies = installedDependencies
        self.downloadDirectory = downloadDirectory
        self.tmpDirectory = joinPaths(self.downloadDirectory,TMP_EXTRACTION_DIRECTORY_NAME)
        if not new_directory(self.tmpDirectory):
            clear_directory_contents(self.tmpDirectory)
    
    def install_dependency(self,dependencyName, version, url, installDirectory):
        downloadDirectory = self.downloadDirectory
        tmpDirectory = self.tmpDirectory
        savePath = download_file(url, downloadDirectory)

        clear_directory_contents(tmpDirectory)
        if extract_file(savePath, tmpDirectory):
            os.remove(savePath)
        else:
            raise Exception("incompatible file type")

        if self.installedDependencies.is_installed(dependencyName):
            self.remove_dependency(dependencyName)

        # not sure wether to add this or not (can cause serious consequences)
        #if os.path.exists(installDirectory):
        #    log("installation directory {i} for dependency {d} already exist, overwriting it...".format(i=installDirectory,d=dependencyName))
        #    shutil.rmtree(installDirectory)
        
        new_directory(installDirectory)

        # if the archive top level contains only one directory,copy its contents(not the directory itself)
        tempDirContents = [name for name in os.listdir(tmpDirectory)]
        if len(tempDirContents) == 1 and os.path.isdir(joinPaths(tmpDirectory,tempDirContents[0])):
            dirPath = joinPaths(tmpDirectory,tempDirContents[0])
            move_directory_contents(dirPath, installDirectory)
            os.rmdir(dirPath)
        else:
            move_directory_contents(tmpDirectory, installDirectory)

        self.installedDependencies.add_dependency(dependencyName, version, installDirectory)
        return True

    def remove_dependency(self, dependencyName):
        installLocation = self.installedDependencies.get_installation_path(dependencyName)
        if os.path.exists(installLocation):
            try:
                shutil.rmtree(installLocation)
            except Exception:
                raise Exception("Error, can't remove {s}, ensure that you have prermissions and the program is not already running".format(s=installLocation))
        else:
            log("directory {s} does not exist, this should happen only if you have deleted the directory manually, please report the problem otherwise".format(s=installLocation))
        self.installedDependencies.remove_dependency(dependencyName)

    def __del__(self):
        shutil.rmtree(self.tmpDirectory)

class InstalledDependencies:
    def __init__(self, data):
        if data is None:
            self.data = {}
        elif self.__validate_schema(data):
            self.data = data
        else:
            raise ValueError("invalid Data")

    def get_dependencies_list(self):
        return self.data.keys()

    def get_installed_version(self, depName):
        assert(self.is_installed(depName))
        return self.data[depName]["version"]

    def get_installation_path(self, depName):
        assert(self.is_installed(depName))
        return self.data[depName]["absolutePath"]

    def remove_dependency(self, dependencyName):
        assert (self.is_installed(dependencyName))
        del self.data[dependencyName]

    def add_dependency(self, depName, version, installationPath):
        assert (version and installationPath)
        assert (not self.is_installed(depName))
        self.data[depName] = {"version":version,"absolutePath":installationPath}

    def is_installed(self, depName, version = None):
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
