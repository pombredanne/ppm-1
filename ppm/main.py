#!/usr/bin/python

import argparse
import os
from distutils.version import StrictVersion
import utility
from config import REQDEPS_FILE_PATH, DEPSINSTALL_DIR_PATH, CURRENTDEPS_FILE_PATH, GENERATED_ENVIRONMENT_PATH
from registryclient import RegistryClient
from repositoryclient import RepositoryClient
from dependencymanager import DependencyManager, InstalledDependencies
from settings import Settings
from environmentmanager import EnvironmentManager

def parseArguments():
    parser = argparse.ArgumentParser(description="Project Package Manager", formatter_class=lambda prog: argparse.ArgumentDefaultsHelpFormatter(prog, width=150, max_help_position=27))

    subparsers = parser.add_subparsers(title='commands', dest='subparser_name')

    parser_sync = subparsers.add_parser('sync', help='synchronize with project dependencies')
    parser_sync.add_argument('--without-install', help="do not install inexistant dependencies", default=False, action='store_true')
    parser_sync.add_argument('--without-update', help="do not update installed packages", default=False, action='store_true')
    parser_sync.add_argument('--without-downgrade', help="do not downgrade packages", default=False, action='store_true')
    parser_sync.add_argument('--without-remove', help="do not remove installed packages which are not present in {d}".format(d=os.path.basename(REQDEPS_FILE_PATH)), default=False, action='store_true')
    parser_sync.set_defaults(func=cmd_sync)

    parser_download = subparsers.add_parser('download', help='download one or more packages(witout installing them)')
    parser_download.add_argument('packages', help="dependencies to download in the format dependencyName@(version|latest)", nargs='+')
    parser_download.add_argument('--directory', help="directory where to download files")
    parser_download.set_defaults(func=cmd_download)

    parser_settingsHandler = subparsers.add_parser('set', help='set a setting')
    parser_settingsHandler.add_argument('setting_name', help="(registry-server|repository-server|project)")
    parser_settingsHandler.add_argument('setting_value', help="option value")
    parser_settingsHandler.set_defaults(func=cmd_set_setting)

    parser_settingsUnsetHandler = subparsers.add_parser('unset', help='unset a setting')
    parser_settingsUnsetHandler.add_argument('setting_name', help="(registry-server|repository-server|project)")
    parser_settingsUnsetHandler.set_defaults(func=cmd_unset_setting)

    args = parser.parse_args()
    args.func(args)


def cmd_sync(args):
    """cmd_sync validate and prepare synchronization operation environment"""
    flags = Flags(install=not args.without_install,
                  update=not args.without_update,
                  downgrade=not args.without_downgrade,
                  remove=not args.without_remove)

    utility.ensure_directory(DEPSINSTALL_DIR_PATH)

    # load currently installed dependencies
    installedDeps = InstalledDependencies(load_installed_deps_file())
    # make sure all dependencies are installed
    check_integrity(installedDeps, DEPSINSTALL_DIR_PATH)
    
    dependencyManager = DependencyManager(installedDeps, DEPSINSTALL_DIR_PATH)

    registryClient = get_registry_client()
    if not registryClient:
        print "registry server is not set, please set it before running ppm"
        return

    settings = Settings()
    if settings.get_current_project():
        project_name = settings.get_current_project()
        try:
            jsonData = registryClient.get_project_details(project_name)
        except Exception as e:
            print "Error occured while retrieving project {p} details from registry server: {e}".format(p=project_name, e=str(e))
            return
    elif os.path.exists(REQDEPS_FILE_PATH):
        try:
            jsonData = utility.load_json_file(REQDEPS_FILE_PATH)
        except Exception as e:
            print "Error occured while reading {f}: {e}".format(f=os.path.basename(REQDEPS_FILE_PATH), e=str(e))
            return            
    else:
        print "unable to fetch dependencies, you have to set a project or create a {d} file".format(d=os.path.basename(REQDEPS_FILE_PATH))
        return

    requiredDeps = RequiredDependencies(jsonData.get('devdependencies',{}))
    
    repositoryClient = get_repository_client()

    # synchronizing dependencies
    sync_dependencies(requiredDeps, installedDeps, registryClient, repositoryClient, dependencyManager, flags)

    # save newly installed packages as current dependencies
    save_installed_deps(installedDeps.get_data())

def cmd_download(args):
    """ downloading one or more packages without monitoring them"""
    downloadDirectory = args.directory or os.getcwd()
    packages = [('@' in p and p.split('@')) or [p,"latest"] for p in args.packages]
    if not os.path.exists(downloadDirectory):
        utility.log("{d} does not exist".format(d=downloadDirectory))
        return

    registryClient = get_registry_client()
    if not registryClient:
        raise Exception("registry server is not set, please set it using set-registry-server command")
    
    repositoryClient = get_repository_client()

    for name, version in packages:
        try:
            package_handler = registryClient.get_package_details(name)
        except Exception as e:
            utility.log(str(e))
            continue

        if version == 'latest':
            version = get_latest_version(package_handler.get_package_versions())
            if version == '0.0':
                utility.log("Package {p} is not in the ppm registry".format(p=name))
                continue
        else:
            version = str(StrictVersion(version))
            if not package_handler.check_version_existence(version):
                utility.log("Package {p} is not in the ppm registry".format(p=name))
                continue

        url = package_handler.get_package_url(version)
        # check for repository url
        if repositoryClient:
            repository_url = repositoryClient.get_package_repository_url(url)
            if repository_url:
                url = repository_url
        utility.download_file(url, downloadDirectory)

def cmd_set_setting(args):
    setting_name = args.setting_name
    setting_value = args.setting_value
    try:
        set_setting(setting_name, setting_value)
        print "{n} has been set to {v}".format(n=setting_name, v=setting_value)
    except Exception as e:
        print str(e)

def cmd_unset_setting(args):
    setting_name = args.setting_name
    try:
        set_setting(setting_name, None)
        print "{n} has been unset".format(n=setting_name)
    except Exception as e:
        print str(e)

def set_setting(setting_name, setting_value):
    settings = Settings()
    if setting_name == "registry-server":
        settings.set_registry_server(setting_value)
    elif setting_name == "repository-server":
        settings.set_repository_server(setting_value)
    elif setting_name == "project":
        settings.set_current_project(setting_value)
    else:
        raise Exception("invalid setting")
    settings.save()
 
# I prefer writing flags.install instead of flags["install"] or installFlag, this class is merely for that purpose
class Flags:
    def __init__(self, install, update, downgrade, remove):
        self.install = install
        self.update = update
        self.downgrade = downgrade
        self.remove = remove

def sync_dependencies(requiredDeps, installedDependencies, registryClient, repositoryClient, dependencyManager, flags):
    """synchronizing installed dependencies with requiredDeps, include installing,updating,downgrading and removing dependencies, in accordance to flags,
    Args:
        requiredDeps: array containing required dependencies for the project, in the format [{depName:version},{depName2,version}]
        installedDependencies: currently installed dependencies
        registryClient: client used for requesting a package details from the registry
        repositoryClient: client used for checking for a package repository url
        DependencyManager: responsible for dependency installation (or remove)
        flags: operations to be performed (can be update, install, downgrade, remove or any combintation of them)
    """

    utility.log("synchronizing dependencies")
    utility.ensure_directory(DEPSINSTALL_DIR_PATH)
    required_dependencies_names = requiredDeps.get_dependencies_names()
    for depName in required_dependencies_names:
        utility.log("Processing {d}".format(d=depName), 1)

        # get current installed version (or set version to 0.0 for new dependencies)
        if installedDependencies.is_installed(depName):
            installedVersion = installedDependencies.get_installed_version(depName)
        else:
            installedVersion = str(StrictVersion('0.0'))

        # get and normalize required version
        requiredVersion = requiredDeps.get_dependency_version(depName)
        requiredVersion = str(StrictVersion(requiredVersion))

        if StrictVersion(requiredVersion) == StrictVersion(installedVersion):
            utility.log("version {v} already installed".format(v=installedVersion))
        elif StrictVersion(requiredVersion) < StrictVersion(installedVersion):
            if flags.downgrade:
                if install_dependency(depName, requiredVersion, dependencyManager, registryClient, repositoryClient):
                    utility.log("{p} version {v} installed successfuly".format(p=depName, v=requiredVersion))
                else:
                    utility.log("{p} installation failed".format(p=depName))
            else:
                utility.log("Required version {v1} < Installed version {v2}, No action taken (downgrade flag is not set)".format(v1=requiredVersion, v2=installedVersion))
        else:
            if (flags.update and StrictVersion(installedVersion) > StrictVersion('0.0')) or (flags.install and StrictVersion(installedVersion) == StrictVersion('0.0')):
                if install_dependency(depName, requiredVersion, dependencyManager, registryClient, repositoryClient):
                    utility.log("{p} version {v} installed successfuly".format(p=depName, v=requiredVersion))
                else:
                    utility.log("{p} installation failed".format(p=depName))
            else:
                utility.log("Required version {v1} > Installed version {v2}, No action taken (update flag is not set)".format(v1=requiredVersion, v2=installedVersion))
        # unident log messages
        utility.log("", -1)

    dependenciesToRemove = [item for item, version in installedDependencies.get_dependencies_list().items() if item not in required_dependencies_names]
    if dependenciesToRemove:
        utility.log("Installed dependencies that are not needed anymore : " + ",".join(dependenciesToRemove))
        if not flags.remove:
            utility.log("ommiting uneeded dependencies (remove flag is not set)")
        else:
            for dependencyName in dependenciesToRemove:
                utility.log("removing {d}".format(d=dependencyName))
                dependencyManager.remove_dependency(dependencyName)

    generate_environment(installedDependencies.get_dependencies_list(), registryClient, os.path.basename(DEPSINSTALL_DIR_PATH), GENERATED_ENVIRONMENT_PATH)
    utility.log("synchronization operation finished")


def install_dependency(name, version, dependencyManager, registryClient, repositoryClient):
    try:
        packageHandler = registryClient.get_package_details(name)
    except Exception as e:
        utility.log(str(e))
        return False

    if not packageHandler.check_version_existence(version):
        utility.log("package {p} version {v} is not in the ppm registry".format(p=name, v=version))

    url = packageHandler.get_package_url(version)
    # check for repository url
    if repositoryClient:
        repository_url = repositoryClient.get_package_repository_url(url)
        if repository_url:
            url = repository_url

    parentDirectoryPath = packageHandler.get_package_parentdir(version)
    directoryName = packageHandler.get_package_dirname(version)
    installDirectoryRelPath = utility.joinPaths(parentDirectoryPath, directoryName)
    try:
        dependencyManager.install_dependency(name, version, url, installDirectoryRelPath)
        return True
    except Exception as e:
        utility.log(str(e))
        return False
    

def generate_environment(dependencies, registryClient, baseDirPath, savePath):
    environment_manager = EnvironmentManager(baseDirPath)
    for name, version in dependencies.items():
        package_details = registryClient.get_package_details(name)
        environment_manager.add_package_env(name, package_details.get_package_env(version))

    utility.ensure_file_directory(savePath)
    with open(savePath, 'w+') as f:
        f.write(environment_manager.generate_script())


def get_registry_client():
    settings = Settings() 
    if settings.get_registry_server():
        return RegistryClient(settings.get_registry_server())


def get_repository_client():
    settings = Settings() 
    if settings.get_repository_server():
        return RepositoryClient(settings.get_repository_server())


def load_installed_deps_file():
    installedDepsContents = None
    if os.path.exists(CURRENTDEPS_FILE_PATH):
        installedDepsContents = utility.load_json_file(CURRENTDEPS_FILE_PATH)
    return installedDepsContents


def save_installed_deps(content):
    utility.ensure_file_directory(CURRENTDEPS_FILE_PATH)
    utility.save_json_to_file(content, CURRENTDEPS_FILE_PATH)

def get_latest_version(availableVersions):
    try:
        availableVersions.sort(key=StrictVersion)
        return str(StrictVersion(availableVersions[-1]))
    except Exception:
        return str(StrictVersion('0.0'))

def check_integrity(installed_dependencies, dependencies_directory):
    installed_paths = dict([(installed_dependencies.get_installation_path(name), name) for name in installed_dependencies.get_dependencies_list().keys()])
    not_found_dirs = [d for d in installed_paths.keys() if not os.path.isdir(os.path.join(dependencies_directory, d))]
    if not_found_dirs:
        print "checking dependencies integrity"
        print "some dependencies directories have been deleted manually:" + str(not_found_dirs)
        for d in not_found_dirs:
            installed_dependencies.remove_dependency(installed_paths[d])
            print "uninstalling " + d

class RequiredDependencies:
    def __init__(self, data):
        if data is None:
            self.data = {}
        elif self.__validate_schema(data):
            self.data = data
        else:
            raise ValueError("invalid Data")

    def get_dependency_version(self, depName):
        assert(self.is_dep_existant(depName))
        return self.data[depName]

    def is_dep_existant(self, depName):
        assert(depName)
        if depName in self.data:
            return True
        return False

    def get_dependencies_names(self):
        return self.data.keys()

    def __validate_schema(self, data):
        # TODO
        return True

if __name__ == "__main__":
    parseArguments()

