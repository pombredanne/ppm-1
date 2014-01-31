import requests
import os

class MirrorClient:

    def __init__(self, server_adress):
        assert server_adress
        self.server_adress = server_adress

    def get_package_mirror_url(self,origin):
        r = requests.post(self.server_adress,origin)
        if r.status_code == 200:
            return r.text