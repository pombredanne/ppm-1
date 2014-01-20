#!/usr/bin/python

import argparse
import os
import urllib2
from distutils.version import StrictVersion
import json
import utility
from dependencymanager import DependencyManager,InstalledDependencies
from mappinghandler import MappingHandler
from urlparse import urljoin
from configmanager import ConfigManager

# relative paths from working directory

# folder that will contains downloaded dependencies
DEPS_FOLDER_NAME = "dependencies"

# json file specifying dependencies to install, used when no explicit install command is specified (explicit ex: pdp install logicblox@3.23)
DEPS_FILE = "dependencies.json"

# downloaded dependencies will be added to this file, this file is used to compare current versions and desired versions in order to determine which packages to install
CURRENT_VERSIONS_FILE = DEPS_FOLDER_NAME + "/current_deps.json"

def parseArguments():
    parser = argparse.ArgumentParser(description="Project Package Manager",formatter_class= lambda prog: argparse.ArgumentDefaultsHelpFormatter(prog, width=150, max_help_position=27))

    subparsers = parser.add_subparsers(title='commands', dest='subparser_name')

    parser_sync = subparsers.add_parser('sync', help='synchronize with {d}'.format(d=DEPS_FILE))
    parser_sync.add_argument('--without-install', help = "do not install inexistant dependencies", default = False, action = 'store_true')
    parser_sync.add_argument('--without-update', help = "do not update installed packages", default = False, action = 'store_true')
    parser_sync.add_argument('--without-downgrade', help = "do not downgrade packages", default = False, action = 'store_true')
    parser_sync.add_argument('--without-remove', help = "do not remove installed packages which are not present in {d}".format(d=DEPS_FILE), default = False, action = 'store_true')
    parser_sync.set_defaults(func=cmd_sync)

    parser_download = subparsers.add_parser('download', help='download one or more files(witout adding them to {d} or monitoring them)'.format(d=DEPS_FILE))
    parser_download.add_argument('dep', help = "dependencies to download in the format dependencyName@(version|latest)", nargs='+')
    parser_download.add_argument('--directory', help = "directory where to download files")
    parser_download.set_defaults(func=cmd_download)

    parser_mirror = subparsers.add_parser('mirror', help='Mirror mapping file')
    parser_mirror.add_argument('remoteDepsMapUrl', help = "remote dependencies map url")
    parser_mirror.add_argument('downloadDirectory', help = "directory where to download files")
    parser_mirror.add_argument('urlPrefix', help = "prefix of file urls", default = "http://127.0.0.1:8000", nargs='?')
    parser_mirror.set_defaults(func=cmd_mirror_packages)

    parser_depsMap = subparsers.add_parser('setdepsmap', help='save dependencies-to-url map file location')
    parser_depsMap.add_argument('depsMapLocation', help = "location of dependencies-to-url map file")
    parser_depsMap.set_defaults(func=cmd_set_deps_map)

    parser.add_argument('--verbose', help = "Enable verbosity", action = 'store_false')
    parser.add_argument('--production', help = "production environment, development is assumed if not present", default= False, action = 'store_true')
    parser.add_argument('--deps-map-location', help = "location of dependencies-to-url map file")

    args = parser.parse_args()
    args.func(args)

def cmd_sync(args):
    depsFile = utility.joinPaths(os.getcwd(),DEPS_FILE)
    if not os.path.exists(depsFile):
        raise Exception("unable to fetch dependencies, {d} file does not exist".format(d=DEPS_FILE))
    jsonData = utility.load_json_file(depsFile)
    if (not args.production and 'devDependencies' not in jsonData) or (args.production and 'prodDependencies' not in jsonData):
        print "no dependencies found"
        return
    deps = jsonData.get('devDependencies')
    flags = Flags(install = not args.without_install,
            update = not args.without_update,
            downgrade = not args.without_downgrade,
            remove = not args.without_remove,
            )
    installedDeps = InstalledDependencies(load_installed_deps_file())

    downloadDirectory = utility.joinPaths(os.getcwd(), DEPS_FOLDER_NAME)
    utility.new_directoryctory(downloadDirectory)
    dependencyManager = DependencyManager(installedDeps, downloadDirectory)
    if args.deps_map_location:
        mappingHandler = download_mapping_handler(args.deps_map_location)
    else:
        mappingHandler = load_mapping_handler()
    sync_dependencies(RequiredDependencies(deps),installedDeps,mappingHandler,dependencyManager, flags)
    save_installed_deps(installedDeps.get_data())

    pass

def cmd_download(args):
    pass

def cmd_mirror_packages(args):
    downloadDirectory = args.downloadDirectory
    remoteDepsMapUrl = args.remoteDepsMapUrl
    urlPrefix = args.urlPrefix
    filePath = utility.joinPaths(downloadDirectory,"depmap.json")

    if not os.path.exists(downloadDirectory):
        utility.log("{d} directory does not exist".format(d=downloadDirectory))
        return

    localMappingHandler = MappingHandler(utility.load_json_file(filePath) if os.path.exists(filePath) else {})
    remoteMappingHandler = download_mapping_handler(remoteDepsMapUrl)
    mirror_map(remoteMappingHandler, localMappingHandler, downloadDirectory, urlPrefix)
    utility.save_json_to_file(localMappingHandler.get_data(), filePath)

def cmd_set_deps_map(args):
    depsMapUrl = args.depsMapLocation
    configManager = ConfigManager()
    configManager.set_deps_map_location(depsMapUrl)
    configManager.save()
    print "deps map location saved successfuly"

# I prefer writing flags.install instead of flags["install"] or installFlag, this class is merely for that purpose
class Flags:
    def __init__(self,install=True,update=True,downgrade=True,remove=True):
        self.install = install
        self.update = update
        self.downgrade = downgrade
        self.remove = remove

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
                    utility.log("Error downloading package {p} version {v}".format(p=remotePackageName,v=remotePackageVersion))
                    continue
            else:
                savePath = localMappingHandler.get_dependency_details(remotePackageName,remotePackageVersion)[0]

            dirName = os.path.basename(os.path.dirname(savePath))
            fileName = os.path.basename(savePath)
            localMappingHandler.add_package(remotePackageName, remotePackageVersion, urljoin(urlPrefix,dirName + '/' + fileName), remoteParentDirectoryPath, remoteDirectoryName, remoteUrl)
    return localMappingHandler

def sync_dependencies(requiredDeps, installedDependencies, depsMap, dependencyManager, flags):
    """synchronizing installed dependencies with requiredDeps, include installing,updating,downgrading and removing dependencies, in accordance to flags,
    Args:
        requiredDeps: array containing required dependencies for the project, in the format [{depName:version},{depName2,version}]
        installedDependencies: currently installed dependencies
        depsMap: map between dependencies and installation information (download url,installLocation...)
        DependencyManager: the Manager responsible for installing dependencies (injected)
        flags: operations to be performed (can be update, install, downgrade, remove or any combintation of them)
    """

    #DIRTY: closure linking sync_dependencies and install_dependency, added because the pattern in used in several places
    def call_install_dependency(dependencyName, version):
        url, parentDirectoryPath, directoryName = depsMap.get_dependency_details(dependencyName, version)
        installDirectoryPath = utility.joinPaths(get_installation_directory_path(), parentDirectoryPath, directoryName if directoryName is not None else dependencyName)
        try:
            dependencyManager.install_dependency(dependencyName, version,url,installDirectoryPath)
            utility.log("{d} installed successfuly".format(d=dependencyName))
        except Exception as e:
            utility.log("a problem occurred while installing {d} : {m}".format(d=dependencyName,m=str(e)))

    utility.log("synchronizing dependencies")
    for depName in requiredDeps.get_dependencies_list():
        utility.log("Processing {d}".format(d=depName),1)
        if installedDependencies.is_installed(depName):
            installedVersion = StrictVersion(installedDependencies.get_installed_version(depName))
        else:
            installedVersion = StrictVersion('0.0')
        reqVersionString = requiredDeps.get_dependency_version(depName)
        if reqVersionString != 'latest':
            requiredVersion = StrictVersion(reqVersionString)
            if requiredVersion == installedVersion:
                utility.log("Required version == Installed version == {v}".format(v=str(installedVersion)))
            elif requiredVersion < installedVersion:
                if flags.downgrade:
                    if depsMap.check_dependency_existence(depName, str(requiredVersion)):
                        call_install_dependency(depName,str(requiredVersion))
                    else:
                        utility.log("{d} version {v} is not found".format(d=depName,v=str(requiredVersion)))
                else:
                    utility.log("Required version {v1} < Installed version {v2}, No action taken (downgrade flag is not set)".format(v1=str(requiredVersion), v2=str(installedVersion)))
            else:
                if (flags.update and installedVersion > StrictVersion('0.0')) or (flags.install and installedVersion == StrictVersion('0.0')):
                    if depsMap.check_dependency_existence(depName, str(requiredVersion)):
                        call_install_dependency(depName,str(requiredVersion))
                    else:
                        utility.log("{d} version {v} is not found".format(d=depName,v=str(requiredVersion)))
                else:
                    utility.log("Required version {v1} > Installed version {v2}, No action taken (update flag is not set)".format(v1=str(requiredVersion), v2=str(installedVersion)))
        else:
            try:
                availableVersions = depsMap.get_versions(depName)
                availableVersions.sort(key=StrictVersion)
                requiredVersion = StrictVersion(availableVersions[-1])
            except Exception:
                utility.log("no versions for {d} are available\n".format(d=depName),-1)
                continue
            if requiredVersion == installedVersion:
                utility.log("Latest version == Installed version == {v}".format(v=str(installedVersion)))
            elif requiredVersion < installedVersion:
                utility.log("Latest version {v1} < Installed version {v2}".format(v1=str(requiredVersion), v2=str(installedVersion)))
                if flags.downgrade:
                    if utility.query_yes_no("do you want to downgrade dependency {d} from version {v1} to version {v2}".format(d=depName, v1=str(installedVersion), v2=str(requiredVersion))):
                        call_install_dependency(depName,str(requiredVersion))
                    else:
                        utility.log("omitting {d}".format(d=depName))
                else:
                    utility.log("No action taken (downgrade flag is not set)")
            else:
                if (flags.update and installedVersion > StrictVersion('0.0')) or (flags.install and installedVersion == StrictVersion('0.0')):
                    call_install_dependency(depName,str(requiredVersion))
                else:
                    utility.log("Required latest version = {v1} > Installed version {v2}, No action taken ({f} flag is not set)".format(v1=str(requiredVersion), v2=str(installedVersion)), f= "install" if installedVersion == StrictVersion('0.0') else "update" )
        # unident log messages
        utility.log("",-1)

    dependenciesToRemove = [item for item in installedDependencies.get_dependencies_list() if item not in requiredDeps.get_dependencies_list()]
    if dependenciesToRemove:
        utility.log("Installed dependencies that are not needed anymore : " + ",".join(dependenciesToRemove))
        if not flags.remove:
            utility.log("ommiting uneeded dependencies (remove flag is not set)")
        else:
            for dependencyName in dependenciesToRemove:
                utility.log("removing {d}".format(d=dependencyName))
                dependencyManager.remove_dependency(dependencyName)
    utility.log("synchronization operation finished")    

def get_installation_directory_path():
    dirct = utility.joinPaths(os.getcwd(), DEPS_FOLDER_NAME)
    if not os.path.exists(dirct):
        os.makedirs(dirct)
    return dirct

def load_mapping_handler():
    config = ConfigManager()
    if config.get_deps_map_location():
        mappingHandler =download_mapping_handler(config.get_deps_map_location())
    elif os.path.exists(utility.joinPaths(os.getcwd(), "depsmap.json")):
        mappingHandler = MappingHandler(utility.load_json_file(utility.joinPaths(os.getcwd(), "depsmap.json")))
    else:
        raise Exception("No dependency-to-url map file specified")
    return mappingHandler

def download_mapping_handler(url):
    assert(url)
    print "download mapping file"
    try:
        response = urllib2.urlopen(urllib2.Request(url))
    except urllib2.HTTPError as e:
        raise Exception("Unable to download mapping file, ", e)
    mappingHandler = MappingHandler(json.load(response))
    response.close()
    return mappingHandler

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

    def is_dep_existant(self,depName):
        assert(depName)
        if depName in self.data:
            return True
        return False

    def get_dependencies_list(self):
        return self.data.keys() 
    
    def __validate_schema(self, data):
        # TODO
        return True

def load_installed_deps_file():
    installedDepsPath = utility.joinPaths(os.getcwd(), CURRENT_VERSIONS_FILE)
    installedDepsContents = None
    if os.path.exists(installedDepsPath):
        installedDepsContents = utility.load_json_file(installedDepsPath)
    return installedDepsContents

def save_installed_deps(content):
    if not content:
        return
    installedDepsPath = utility.joinPaths(os.getcwd(), CURRENT_VERSIONS_FILE)
    utility.save_json_to_file(content,installedDepsPath)

if __name__ == "__main__":
    parseArguments()