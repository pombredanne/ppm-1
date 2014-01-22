#!/usr/bin/python

import argparse
import os
import urllib2
from distutils.version import StrictVersion
import json
import utility
from dependencymanager import DependencyManager, InstalledDependencies
from mappinghandler import MappingHandler
from settings import Settings
from config import REQDEPS_FILE_PATH, DEPSINSTALL_DIR_PATH, CURRENTDEPS_FILE_PATH, DEPSINFO_FILE_PATH
import server


def parseArguments():
    parser = argparse.ArgumentParser(description="Project Package Manager", formatter_class=lambda prog: argparse.ArgumentDefaultsHelpFormatter(prog, width=150, max_help_position=27))

    subparsers = parser.add_subparsers(title='commands', dest='subparser_name')

    parser_sync = subparsers.add_parser('sync', help='synchronize with {d}'.format(d=REQDEPS_FILE_PATH))
    parser_sync.add_argument('--without-install', help="do not install inexistant dependencies", default=False, action='store_true')
    parser_sync.add_argument('--without-update', help="do not update installed packages", default=False, action='store_true')
    parser_sync.add_argument('--without-downgrade', help="do not downgrade packages", default=False, action='store_true')
    parser_sync.add_argument('--without-remove', help="do not remove installed packages which are not present in {d}".format(d=REQDEPS_FILE_PATH), default=False, action='store_true')
    parser_sync.set_defaults(func=cmd_sync)

    parser_download = subparsers.add_parser('download', help='download one or more files(witout adding them to {d} or monitoring them)'.format(d=REQDEPS_FILE_PATH))
    parser_download.add_argument('packages', help="dependencies to download in the format dependencyName@(version|latest)", nargs='+')
    parser_download.add_argument('--directory', help="directory where to download files")
    parser_download.set_defaults(func=cmd_download)

    parser_mirror = subparsers.add_parser('run-mirror-server', help='run a HTTP Mirror server (serving packages)')
    parser_mirror.add_argument('host', help="host adress")
    parser_mirror.add_argument('port', help="port to run on")
    parser_mirror.set_defaults(func=cmd_run_mirror_server)

    parser_mirror = subparsers.add_parser('update-mirror', help='update Mirror server with a dependencies-info')
    parser_mirror.add_argument('remoteServer', help="remote server ip")
    parser_mirror.add_argument('localDepsMap', help="dependencies-info file")
    parser_mirror.set_defaults(func=cmd_update_mirror)

    parser_depsMap = subparsers.add_parser('set-mirror', help='set and save mirror server')
    parser_depsMap.add_argument('server', help="mirror server in the format 127.0.0.1:8000")
    parser_depsMap.set_defaults(func=cmd_set_mirror)

    parser.add_argument('--verbose', help="Enable verbosity", action='store_false')
    parser.add_argument('--production', help="production environment, development is assumed if not present", default=False, action='store_true')
    parser.add_argument('--mirror', help="set mirror server where to fetchdependencies")

    args = parser.parse_args()
    args.func(args)


# cmd_sampleFunction is responsible for validating commandline arguments and loading sampleFunction dependencies(parameters of sampleFunction)
def cmd_sync(args):
    if not os.path.exists(REQDEPS_FILE_PATH):
        raise Exception("unable to fetch dependencies, {d} file does not exist".format(d=REQDEPS_FILE_PATH))
    jsonData = utility.load_json_file(REQDEPS_FILE_PATH)
    if (not args.production and 'devDependencies' not in jsonData) or (args.production and 'prodDependencies' not in jsonData):
        print "no dependencies found"
        return
    deps = jsonData.get('devDependencies')
    flags = Flags(install=not args.without_install,
                  update=not args.without_update,
                  downgrade=not args.without_downgrade,
                  remove=not args.without_remove)

    # load dependencies-info data
    if args.mirror:
        mappingHandler = download_mapping_handler(args.mirror)
    else:
        mappingHandler = load_mapping_handler()

    utility.ensure_directory(DEPSINSTALL_DIR_PATH)

    # load currently installed dependencies
    installedDeps = InstalledDependencies(load_installed_deps_file())

    dependencyManager = DependencyManager(installedDeps, DEPSINSTALL_DIR_PATH)

    # synchronizing dependencies
    sync_dependencies(RequiredDependencies(deps), installedDeps, mappingHandler, dependencyManager, flags)

    # save newly installed packages as current dependencies
    save_installed_deps(installedDeps.get_data())


def cmd_download(args):
    """ downloading one or more packages without monitoring them, this is meant for downloading from a local repositry """
    downloadDirectory = args.directory
    packages = [('@' in p and p.split('@')) or [p,"latest"] for p in args.packages]
    if not os.path.exists(downloadDirectory):
        utility.log("{d} does not exist".format(d=downloadDirectory))
        return

    mappingHandler = load_mapping_handler()
    for name, version in packages:
        if version == 'latest':
            version = get_latest_version(name, mappingHandler)
            if version == '0.0':
                utility.log("{p} is not available\n".format(p=name))
                continue
        else:
            try:
                version = str(StrictVersion(version))
            except Exception:
                utility.log("invalid version {s}".format(s=version))
                continue
            if not mappingHandler.check_dependency_existence(name, version):
                utility.log("{p} version {v} is not available\n".format(p=name, v=version))
                continue
        url = mappingHandler.get_dependency_details(name, version)[0]
        utility.download_file(url, downloadDirectory)


def cmd_run_mirror_server(args):
    server.run_server(args.host, int(args.port))


def cmd_update_mirror(args):
    remoteServer = args.remoteServer
    localDepsMap = args.localDepsMap

    if not os.path.exists(localDepsMap):
        utility.log("{d} does not exist".format(d=localDepsMap))
        return
    
    jsonData = utility.load_json_file(localDepsMap)
    if jsonData:
        utility.post_json_data(jsonData, remoteServer)


def cmd_set_mirror(args):
    server = args.server
    settings = Settings()
    settings.set_deps_map_location(server)
    settings.save()
    print "deps map location saved successfuly"


# I prefer writing flags.install instead of flags["install"] or installFlag, this class is merely for that purpose
class Flags:
    def __init__(self, install, update, downgrade, remove):
        self.install = install
        self.update = update
        self.downgrade = downgrade
        self.remove = remove


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
        installDirectoryPath = utility.joinPaths(DEPSINSTALL_DIR_PATH, parentDirectoryPath, directoryName if directoryName is not None else dependencyName)
        try:
            dependencyManager.install_dependency(dependencyName, version, url, installDirectoryPath)
            utility.log("{d} installed successfuly".format(d=dependencyName))
        except Exception as e:
            utility.log("a problem occurred while installing {d} : {m}".format(d=dependencyName, m=str(e)))

    utility.log("synchronizing dependencies")
    utility.ensure_directory(DEPSINSTALL_DIR_PATH)

    for depName in requiredDeps.get_dependencies_list():
        utility.log("Processing {d}".format(d=depName), 1)
        if installedDependencies.is_installed(depName):
            installedVersion = installedDependencies.get_installed_version(depName)
        else:
            installedVersion = str(StrictVersion('0.0'))
        requiredVersion = requiredDeps.get_dependency_version(depName)
        if requiredVersion != 'latest':
            requiredVersion = str(StrictVersion(requiredVersion))
            if StrictVersion(requiredVersion) == StrictVersion(installedVersion):
                utility.log("Required version == Installed version == {v}".format(v=installedVersion))
            elif StrictVersion(requiredVersion) < StrictVersion(installedVersion):
                if flags.downgrade:
                    if depsMap.check_dependency_existence(depName, requiredVersion):
                        call_install_dependency(depName, requiredVersion)
                    else:
                        utility.log("{d} version {v} is not found".format(d=depName, v=requiredVersion))
                else:
                    utility.log("Required version {v1} < Installed version {v2}, No action taken (downgrade flag is not set)".format(v1=requiredVersion, v2=installedVersion))
            else:
                if (flags.update and StrictVersion(installedVersion) > StrictVersion('0.0')) or (flags.install and StrictVersion(installedVersion) == StrictVersion('0.0')):
                    if depsMap.check_dependency_existence(depName, requiredVersion):
                        call_install_dependency(depName, requiredVersion)
                    else:
                        utility.log("{d} version {v} is not found".format(d=depName, v=requiredVersion))
                else:
                    utility.log("Required version {v1} > Installed version {v2}, No action taken (update flag is not set)".format(v1=requiredVersion, v2=installedVersion))
        else:
            requiredVersion = get_latest_version(depName, depsMap)
            if StrictVersion(requiredVersion) == StrictVersion('0.0'):
                utility.log("no versions for {d} are available\n".format(d=depName), -1)
                continue
            if StrictVersion(requiredVersion) == StrictVersion(installedVersion):
                utility.log("Latest version == Installed version == {v}".format(v=installedVersion))
            elif StrictVersion(requiredVersion) < StrictVersion(installedVersion):
                utility.log("Latest version {v1} < Installed version {v2}".format(v1=requiredVersion, v2=installedVersion))
                if flags.downgrade:
                    if utility.query_yes_no("do you want to downgrade dependency {d} from version {v1} to version {v2}".format(d=depName, v1=installedVersion, v2=requiredVersion)):
                        call_install_dependency(depName, requiredVersion)
                    else:
                        utility.log("omitting {d}".format(d=depName))
                else:
                    utility.log("No action taken (downgrade flag is not set)")
            else:
                if (flags.update and StrictVersion(installedVersion) > StrictVersion('0.0')) or (flags.install and StrictVersion(installedVersion) == StrictVersion('0.0')):
                    call_install_dependency(depName, requiredVersion)
                else:
                    utility.log("Required latest version = {v1} > Installed version {v2}, No action taken ({f} flag is not set)".format(v1=requiredVersion, v2=installedVersion), f="install" if StrictVersion(installedVersion) == StrictVersion('0.0') else "update")
        # unident log messages
        utility.log("", -1)

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

def load_mapping_handler():
    settings = Settings()
    if settings.get_deps_map_location():
        mappingHandler = download_mapping_handler(settings.get_deps_map_location())
    elif os.path.exists(DEPSINFO_FILE_PATH):
        mappingHandler = MappingHandler(utility.load_json_file(DEPSINFO_FILE_PATH))
    else:
        raise Exception("No dependency-to-url map file specified")
    return mappingHandler


def download_mapping_handler(url):
    assert(url)
    print "download mapping file"
    try:
        response = urllib2.urlopen(urllib2.Request(url))
    except urllib2.HTTPError as e:
        raise Exception("Unable to download mapping file from {u}, ".format(u=url), str(e))
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

    def is_dep_existant(self, depName):
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
    installedDepsContents = None
    if os.path.exists(CURRENTDEPS_FILE_PATH):
        installedDepsContents = utility.load_json_file(CURRENTDEPS_FILE_PATH)
    return installedDepsContents


def save_installed_deps(content):
    if content:
        utility.ensure_file_directory(CURRENTDEPS_FILE_PATH)
        utility.save_json_to_file(content, CURRENTDEPS_FILE_PATH)


def get_latest_version(depName, depsinfo):
    try:
        availableVersions = depsinfo.get_versions(depName)
        availableVersions.sort(key=StrictVersion)
        return str(StrictVersion(availableVersions[-1]))
    except Exception:
        return str(StrictVersion('0.0'))

if __name__ == "__main__":
    parseArguments()
