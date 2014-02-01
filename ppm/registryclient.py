import requests
import os
from packagehandler import PackageHandler
from config import REQUEST_TIMEOUT

PACKAGES_DATABASE = 'packages'
PROJECTS_DATABASE = 'projects'

class RegistryClient:
    def __init__(self, server_adress):
        assert server_adress
        self.server_adress = server_adress
        self.packages = {}

    def get_package_details(self, packageName):
        assert packageName
        # check if the project details are already in cache
        if packageName in self.packages:
            return PackageHandler(self.packages[packageName])
        # download package details from registry
        url = os.path.join(self.server_adress,PACKAGES_DATABASE,packageName)
        r = requests.get(url, timeout=REQUEST_TIMEOUT)
        if r.status_code == 404:
            raise Exception("Package {p} is not in the ppm packages registry".format(p=packageName))
        r.raise_for_status()

        res_data = r.json()
        self.packages[packageName] = res_data
        return PackageHandler(res_data)

    def get_project_details(self, projectName):
        assert projectName
        url = os.path.join(self.server_adress,PROJECTS_DATABASE,projectName)
        r = requests.get(url, timeout=REQUEST_TIMEOUT)
        if r.status_code == 404:
            raise Exception("Project {p} is not in the ppm projects registry".format(p=projectName))
        r.raise_for_status()
        return r.json()