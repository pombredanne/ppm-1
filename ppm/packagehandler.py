import utility
class PackageHandler:
    def __init__(self, data):
        if data is None:
            self.data = {}
        elif self.__validate_schema(data):
            self.data = data
        else:
            raise ValueError("invalid data")

    def get_package_versions(self):
        if "versions" in self.data:
            return self.data["versions"].keys()
        else:
            return []

    def get_package_url(self, version):
        assert self.check_version_existence(version)
        if "url" in self.data["versions"][version]:
            return self.data["versions"][version]["url"] 

    def get_package_env(self, version):
        env = self.__get_attribute("env", version)
        if not env:
            return
        parent_package = self.get_package_parentdir(version)
        dir_name = self.get_package_dirname(version)
        dir_path = utility.joinPaths(parent_package, dir_name)            
        return [s.replace("${HOME}","${DEPS_HOME}/"+dir_path) for s in list(env)]

    def get_package_dirname(self, version):
        return self.__get_attribute("directoryname", version) or self.__get_attribute("_id", version)

    def get_package_parentdir(self, version):
        return self.__get_attribute("parentdirectorypath", version)

    def check_version_existence(self, version):
        assert version
        return version in self.get_package_versions()

    def __get_attribute(self, attribute, version):
        assert attribute and self.check_version_existence(version)
        if version and attribute in self.data["versions"][version]:
            return self.data["versions"][version][attribute]
        elif attribute in self.data:
            return self.data[attribute]

    def __validate_schema(self, data):
        # TODO
        return True
