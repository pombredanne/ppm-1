from mappinghandler import MappingHandler
import unittest
import os
import shutil
from utility import *

class TestMappingHandler(unittest.TestCase):
    
    def test_methods(self):
        mappingHandler = MappingHandler({})
        self.assertEqual(len(mappingHandler.get_packages()), 0)

        packageUrl = "http://127.0.0.1:8000/tests/testpackages/logicblox.tar.gz"
        packageOrigin = "http://logicblox.com/lb.tar.gz"

        mappingHandler.add_package("logicblox", "1.0.0", packageUrl,"tools","lb", packageOrigin)

        self.assertTrue(mappingHandler.check_dependency_existence("logicblox"))
        self.assertEqual(mappingHandler.get_dependency_details("logicblox", "1.0"),(packageUrl, "tools", "lb"))
        self.assertEqual(mappingHandler.get_origin("logicblox", "1.0"),packageOrigin)
        self.assertEqual(len(mappingHandler.get_packages()), 1)
        
        mappingHandler.add_package("logicblox", "2.0", packageUrl,"tools","lb", packageOrigin)

        self.assertEqual(set(mappingHandler.get_versions("logicblox")),set(["1.0","2.0"]))

if __name__ == '__main__':
    unittest.main()