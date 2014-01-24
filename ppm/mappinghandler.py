import utility
from distutils.version import StrictVersion
import os


class MappingHandler:
    def __init__(self, data):
        if data is None:
            self.data = {}
        elif self.__validate_schema(data):
            self.data = data
        else:
            raise ValueError("invalid data")

    def get_dependency_details(self, depName, depVersion):
        assert(depName and depVersion and self.check_dependency_existence(depName, depVersion))
        depDetails = self.data[depName][depVersion]

        parentDirectoryPath = depDetails["parentDirectoryPath"] if "parentDirectoryPath" in depDetails else None
        directoryName = depDetails["directoryName"] if "directoryName" in depDetails else None
        url = depDetails["url"] if "url" in depDetails else None

        if (not utility.secure_against_path_traversal(parentDirectoryPath)) or (not utility.secure_against_path_traversal(directoryName)):
            raise Exception("possible File Traversal Attack caused by {s}".format(s=utility.joinPaths(parentDirectoryPath, directoryName)))

        return url, parentDirectoryPath, directoryName

    def get_packages(self):
        return self.data.keys()

    def add_package(self, dependencyName, dependencyVersion, url, parentDirectoryPath=None, directoryName=None, origin=None):
        if (not utility.secure_against_path_traversal(parentDirectoryPath)) or (not utility.secure_against_path_traversal(directoryName)):
            raise Exception("possible File Traversal Attack caused by {s}".format(s=utility.joinPaths(parentDirectoryPath, directoryName)))
        if not url:
            raise Exception("invalid url")
        if not dependencyName:
            raise Exception("invalid dependency name")
        dependencyVersion = str(StrictVersion(dependencyVersion))
        dependencyDetails = {"url": url}
        if parentDirectoryPath is not None:
            dependencyDetails["parentDirectoryPath"] = parentDirectoryPath
        if directoryName is not None:
            dependencyDetails["directoryName"] = directoryName
        if origin is not None:
            dependencyDetails["origin"] = origin

        if dependencyName not in self.data:
            self.data[dependencyName] = {}
        self.data[dependencyName][dependencyVersion] = dependencyDetails

    def get_versions(self, packageName):
        assert(packageName)
        if not self.check_dependency_existence(packageName):
            raise Exception("package {p} not found".format(p=packageName))
        return self.data[packageName].keys()

    def get_origin(self, packageName, version):
        if not self.check_dependency_existence(packageName, version):
            raise Exception("package {p} version {v} not found".format(p=packageName, v=version))
        return self.data[packageName][version]["origin"]

    def check_dependency_existence(self, depName, version=None):
        assert(depName)
        if depName in self.data and (version is None or version in self.get_versions(depName)):
            return True
        return False

    def get_data(self):
        return dict(self.data)

    def __validate_schema(self, data):
        # TODO
        return True
