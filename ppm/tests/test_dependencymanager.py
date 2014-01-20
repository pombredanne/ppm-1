from dependencymanager import DependencyManager, InstalledDependencies
import unittest
import os
import shutil
import utility

class TestInstalledDependencies(unittest.TestCase):

    def setUp(self):
        self.feedData = {"lb": {"version": "4.0", "absolutePath": "/test/installed/lb"}, "bloxweb": {"version": "1.0.0", "absolutePath": "/test/inestalled/bloxweb"}, "java": {"version": "7.0.5", "absolutePath": "/test/inestalled/java"}}

    def test_methods(self):
        installedDependencies = InstalledDependencies(self.feedData)
        
        self.assertEqual(len(installedDependencies.get_dependencies_list()), 3)
        self.assertTrue(installedDependencies.is_installed("java"))
        
        installedDependencies.remove_dependency("java")
        self.assertFalse(installedDependencies.is_installed("java"))
        self.assertEqual(len(installedDependencies.get_dependencies_list()), 2)
        
        installedDependencies.add_dependency("node","0.1","/test/installed/node")
        self.assertTrue(installedDependencies.is_installed("node"))
        self.assertTrue(installedDependencies.is_installed("node", "0.1"))
        self.assertFalse(installedDependencies.is_installed("node","0.1.2"))
        self.assertEqual(len(installedDependencies.get_dependencies_list()), 3)
        self.assertEqual(installedDependencies.get_installed_version("node"), "0.1")
        self.assertEqual(installedDependencies.get_installation_path("node"), "/test/installed/node")

class TestDependencyManager(unittest.TestCase):

    def setUp(self):
        self.currentDirectoryPath = os.path.dirname(os.path.realpath(__file__))
        self.depsDirectorypath = utility.joinPaths(self.currentDirectoryPath,"tmpdeps")
        utility.new_directory(self.depsDirectorypath) or utility.clear_directory_contents(self.depsDirectorypath)

    def test_methods(self):
        installedDependencies = InstalledDependencies({})

        dependencyManager = DependencyManager(installedDependencies, self.depsDirectorypath)

        dependencyManager.install_dependency("angular","0.1","http://127.0.0.1:8000/tests/testpackages/angular.js-master.zip",utility.joinPaths(self.depsDirectorypath,"angularjs"))
        self.assertTrue(installedDependencies.is_installed("angular"))
        self.assertEqual(installedDependencies.get_installed_version("angular"),"0.1")
        self.assertEqual(installedDependencies.get_installation_path("angular"), utility.joinPaths(self.depsDirectorypath,"angularjs"))
        self.assertTrue(os.path.exists(utility.joinPaths(self.depsDirectorypath,"angularjs")))

        dependencyManager.install_dependency("angular","0.2","http://127.0.0.1:8000/tests/testpackages/angular.js-master.zip",utility.joinPaths(self.depsDirectorypath,"angular"))
        self.assertTrue(installedDependencies.is_installed("angular"))
        self.assertEqual(installedDependencies.get_installed_version("angular"),"0.2")
        self.assertEqual(installedDependencies.get_installation_path("angular"), utility.joinPaths(self.depsDirectorypath,"angular"))
        self.assertTrue(os.path.exists(utility.joinPaths(self.depsDirectorypath,"angular")))
        self.assertFalse(os.path.exists(utility.joinPaths(self.depsDirectorypath,"angularjs")))

        dependencyManager.remove_dependency("angular")
        self.assertFalse(installedDependencies.is_installed("angular"))
        self.assertFalse(os.path.exists(utility.joinPaths(self.depsDirectorypath,"angular")))

    def tearDown(self):
        shutil.rmtree(self.depsDirectorypath)

if __name__ == '__main__':
    unittest.main()