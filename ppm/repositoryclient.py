import requests
import os
from config import REQUEST_TIMEOUT
from utility import log
class RepositoryClient:

    def __init__(self, server_adress):
        assert server_adress
        self.server_adress = server_adress

    def get_package_repository_url(self,origin):
        try:
            r = requests.post(self.server_adress,origin,timeout=REQUEST_TIMEOUT)
            if r.status_code == 200:
                return r.text
            elif r.status_code == 404:
                log("file not found in the repository")
        except requests.exceptions.RequestException as e:
            log("Connection error to repository server, "+self.server_adress+": "+str(e))
            return None
