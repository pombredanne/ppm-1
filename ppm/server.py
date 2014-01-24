from SimpleHTTPServer import SimpleHTTPRequestHandler
from BaseHTTPServer import HTTPServer
import time
import json
import utility
import os
from mappinghandler import MappingHandler
from config import DOWNLOAD_DIR_REL_PATH, DEPSINFO_FILE_REL_PATH, DEFAULT_HOST_ADRESS, DEFAULT_PORT_NUMBER
from urlparse import urljoin

host_adress = None
port_number = None

class ppmRequestHandler(SimpleHTTPRequestHandler):
    def do_POST(self):
        """Serve a Post request."""
        try:
            length = int(self.headers.getheader('content-length'))
            data = self.rfile.read(length)
            process_data(data, self.client_address)
            self.send_response(200, "OK")
        except Exception as exc:
            utility.log(str(exc))
            self.send_response(200, str(exc))
        finally:
            self.finish()
    def do_GET(self):
        """Serve a GET request."""
        # simple rewriteRule to seperate request url from physical resource
        if self.path == '/dependencies-info':
            self.path = '/dependecies-info.json'

        f = self.send_head()
        if f:
            self.copyfile(f, self.wfile)
            f.close()



def process_data(data, client_address):
        utility.ensure_directory(DOWNLOAD_DIR_REL_PATH)
        utility.ensure_file_directory(DEPSINFO_FILE_REL_PATH)
        dataMappingHandler = MappingHandler(json.loads(data))
        localMappingHandler = MappingHandler(utility.load_json_file(DEPSINFO_FILE_REL_PATH) if os.path.exists(DEPSINFO_FILE_REL_PATH) else {})
        mirror_map(dataMappingHandler, localMappingHandler, DOWNLOAD_DIR_REL_PATH, "http://"+host_adress+":"+str(port_number))
        utility.save_json_to_file(localMappingHandler.get_data(), DEPSINFO_FILE_REL_PATH)



def mirror_map(sourceMappingHandler, localMappingHandler, downloadDirectory, urlPrefix):
    for remotePackageName in sourceMappingHandler.get_packages():
        for remotePackageVersion in sourceMappingHandler.get_versions(remotePackageName):
            utility.log("processing {p} version {v}".format(p=remotePackageName, v=remotePackageVersion),1)
            remoteUrl, remoteParentDirectoryPath, remoteDirectoryName = sourceMappingHandler.get_dependency_details(remotePackageName, remotePackageVersion)
            
            # get origin url of package (from where the package was downloaded)
            localPackageOrigin = None
            if localMappingHandler.check_dependency_existence(remotePackageName, remotePackageVersion):
                localPackageOrigin = localMappingHandler.get_origin(remotePackageName, remotePackageVersion)
            
            # check if the package was already downloaded from the same source
            if remoteUrl != localPackageOrigin:
                try:
                    utility.log("downloading package from {u}".format(u=remoteUrl))
                    savePath = utility.download_file(remoteUrl, downloadDirectory, allowRedirection=False)
                    utility.log("package downloaded successefuly")
                except Exception as e:
                    utility.log("Error downloading package")
                    utility.log(str(e),-1)
                    continue
            else:
                utility.log("package already exists, updating details")
                savePath = localMappingHandler.get_dependency_details(remotePackageName, remotePackageVersion)[0]

            dirName = os.path.basename(os.path.dirname(savePath))
            fileName = os.path.basename(savePath)
            localMappingHandler.add_package(remotePackageName, remotePackageVersion, urljoin(urlPrefix, dirName + '/' + fileName), remoteParentDirectoryPath, remoteDirectoryName, remoteUrl)
            utility.log("package processed successefuly".format(p=remotePackageName), -1)
    return localMappingHandler

def run_server(host=DEFAULT_HOST_ADRESS, port=DEFAULT_PORT_NUMBER):
    global host_adress, port_number
    host_adress = host
    port_number = port
    httpd = HTTPServer((host_adress, port_number), ppmRequestHandler)
    print time.asctime(), "Server Starts - %s:%s" % (host_adress, port_number)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    httpd.server_close()
    print time.asctime(), "Server Stops - %s:%s" % (host_adress, port_number)
