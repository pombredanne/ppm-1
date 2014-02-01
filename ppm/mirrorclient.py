import requests
import os
from config import REQUEST_TIMEOUT
from utility import log
class MirrorClient:

    def __init__(self, server_adress):
        assert server_adress
        self.server_adress = server_adress

    def get_package_mirror_url(self,origin):
        try:
            r = requests.post(self.server_adress,origin,timeout=REQUEST_TIMEOUT)
            if r.status_code == 200:
                return r.text            
        except requests.exceptions.RequestException as e:
            log("Connection error to mirror server, "+self.server_adress+": "+str(e))
            return None
