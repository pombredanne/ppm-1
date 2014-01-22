from SimpleHTTPServer import SimpleHTTPRequestHandler
from BaseHTTPServer import HTTPServer
import time
import json
import utility
import os
from mappinghandler import MappingHandler, mirror_map
from config import DOWNLOAD_DIR_REL_PATH, DEPSINFO_FILE_REL_PATH, DEFAULT_HOST_ADRESS, DEFAULT_PORT_NUMBER


host_adress = None
port_number = None

class ppmRequestHandler(SimpleHTTPRequestHandler):
    def do_POST(self):
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


def process_data(data, client_address):
        utility.ensure_directory(DOWNLOAD_DIR_REL_PATH)
        utility.ensure_file_directory(DEPSINFO_FILE_REL_PATH)
        dataMappingHandler = MappingHandler(json.loads(data))
        localMappingHandler = MappingHandler(utility.load_json_file(DEPSINFO_FILE_REL_PATH) if os.path.exists(DEPSINFO_FILE_REL_PATH) else {})
        mirror_map(dataMappingHandler, localMappingHandler, DOWNLOAD_DIR_REL_PATH, "http://"+host_adress+":"+str(port_number))
        utility.save_json_to_file(localMappingHandler.get_data(), DEPSINFO_FILE_REL_PATH)


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
