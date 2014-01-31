import requests
import os
from packagehandler import PackageHandler

PACKAGES_NAMES = 'packagesnames' 
PACKAGE_INFO = 'package'

class RegistryClient:
    def __init__(self, server_adress):
        assert server_adress
        self.server_adress = server_adress
        self.packages = {}

    def get_packages_names(self):
        url = os.path.join(self.server_adress,PACKAGES_NAMES)
        r = requests.get(url)
        data = r.json()
        return [item.value for item in data.rows]

    def get_package_details(self, packageName):
        assert packageName
        # check if the project details are already in cache
        if packageName in self.packages:
            return PackageHandler(self.packages[packageName])
        # download package details from registry
        url = os.path.join(self.server_adress,PACKAGE_INFO,packageName)
        r = requests.get(url)
        if r.status_code == 404:
            raise Exception("Package {p} is not in the ppm registry".format(p=packageName))
        r.raise_for_status()

        res_data = r.json()
        self.packages[packageName] = res_data
        return PackageHandler(res_data)