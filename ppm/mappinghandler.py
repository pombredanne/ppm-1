import utility
from distutils.version import StrictVersion
import os
from urlparse import urljoin

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



def mirror_map(sourceMappingHandler, localMappingHandler, downloadDirectory, urlPrefix):
    for remotePackageName in sourceMappingHandler.get_packages():
        for remotePackageVersion in sourceMappingHandler.get_versions(remotePackageName):
            remoteUrl, remoteParentDirectoryPath, remoteDirectoryName = sourceMappingHandler.get_dependency_details(remotePackageName, remotePackageVersion)
            localPackageOrigin = None
            if localMappingHandler.check_dependency_existence(remotePackageName, remotePackageVersion):
                localPackageOrigin = localMappingHandler.get_origin(remotePackageName, remotePackageVersion)
            if remoteUrl != localPackageOrigin:
                try:
                    utility.log("downloading package {p} version {v}".format(p=remotePackageName, v=remotePackageVersion))
                    savePath = utility.download_file(remoteUrl, downloadDirectory)
                except Exception:
                    utility.log("Error downloading package {p} version {v}".format(p=remotePackageName, v=remotePackageVersion))
                    continue
            else:
                savePath = localMappingHandler.get_dependency_details(remotePackageName, remotePackageVersion)[0]

            dirName = os.path.basename(os.path.dirname(savePath))
            fileName = os.path.basename(savePath)
            localMappingHandler.add_package(remotePackageName, remotePackageVersion, urljoin(urlPrefix, dirName + '/' + fileName), remoteParentDirectoryPath, remoteDirectoryName, remoteUrl)
            utility.log("package {p} added successefuly".format(p=remotePackageName))
    return localMappingHandler