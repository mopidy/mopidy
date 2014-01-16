from __future__ import unicode_literals

import platform
import mock
import unittest

import pygst
pygst.require('0.10')
import gst

import pkg_resources

from mopidy.utils import deps


class DepsTest(unittest.TestCase):
    def test_format_dependency_list(self):
        adapters = [
            lambda: dict(name='Python', version='FooPython 2.7.3'),
            lambda: dict(name='Platform', version='Loonix 4.0.1'),
            lambda: dict(
                name='Pykka', version='1.1',
                path='/foo/bar', other='Quux'),
            lambda: dict(name='Foo'),
            lambda: dict(name='Mopidy', version='0.13', dependencies=[
                dict(name='pylast', version='0.5', dependencies=[
                    dict(name='setuptools', version='0.6')
                ])
            ])
        ]

        result = deps.format_dependency_list(adapters)

        self.assertIn('Python: FooPython 2.7.3', result)

        self.assertIn('Platform: Loonix 4.0.1', result)

        self.assertIn('Pykka: 1.1 from /foo/bar', result)
        self.assertNotIn('/baz.py', result)
        self.assertIn('Detailed information: Quux', result)

        self.assertIn('Foo: not found', result)

        self.assertIn('Mopidy: 0.13', result)
        self.assertIn('  pylast: 0.5', result)
        self.assertIn('    setuptools: 0.6', result)

    def test_platform_info(self):
        result = deps.platform_info()

        self.assertEquals('Platform', result['name'])
        self.assertIn(platform.platform(), result['version'])

    def test_python_info(self):
        result = deps.python_info()

        self.assertEquals('Python', result['name'])
        self.assertIn(platform.python_implementation(), result['version'])
        self.assertIn(platform.python_version(), result['version'])
        self.assertIn('python', result['path'])
        self.assertNotIn('platform.py', result['path'])

    def test_gstreamer_info(self):
        result = deps.gstreamer_info()

        self.assertEquals('GStreamer', result['name'])
        self.assertEquals(
            '.'.join(map(str, gst.get_gst_version())), result['version'])
        self.assertIn('gst', result['path'])
        self.assertNotIn('__init__.py', result['path'])
        self.assertIn('Python wrapper: gst-python', result['other'])
        self.assertIn(
            '.'.join(map(str, gst.get_pygst_version())), result['other'])
        self.assertIn('Relevant elements:', result['other'])

    @mock.patch('pkg_resources.get_distribution')
    def test_pkg_info(self, get_distribution_mock):
        dist_mopidy = mock.Mock()
        dist_mopidy.project_name = 'Mopidy'
        dist_mopidy.version = '0.13'
        dist_mopidy.location = '/tmp/example/mopidy'
        dist_mopidy.requires.return_value = ['Pykka']

        dist_pykka = mock.Mock()
        dist_pykka.project_name = 'Pykka'
        dist_pykka.version = '1.1'
        dist_pykka.location = '/tmp/example/pykka'
        dist_pykka.requires.return_value = ['setuptools']

        dist_setuptools = mock.Mock()
        dist_setuptools.project_name = 'setuptools'
        dist_setuptools.version = '0.6'
        dist_setuptools.location = '/tmp/example/setuptools'
        dist_setuptools.requires.return_value = []

        get_distribution_mock.side_effect = [
            dist_mopidy, dist_pykka, dist_setuptools]

        result = deps.pkg_info()

        self.assertEquals('Mopidy', result['name'])
        self.assertEquals('0.13', result['version'])
        self.assertIn('mopidy', result['path'])

        dep_info_pykka = result['dependencies'][0]
        self.assertEquals('Pykka', dep_info_pykka['name'])
        self.assertEquals('1.1', dep_info_pykka['version'])

        dep_info_setuptools = dep_info_pykka['dependencies'][0]
        self.assertEquals('setuptools', dep_info_setuptools['name'])
        self.assertEquals('0.6', dep_info_setuptools['version'])

    @mock.patch('pkg_resources.get_distribution')
    def test_pkg_info_for_missing_dist(self, get_distribution_mock):
        get_distribution_mock.side_effect = pkg_resources.DistributionNotFound

        result = deps.pkg_info()

        self.assertEquals('Mopidy', result['name'])
        self.assertNotIn('version', result)
        self.assertNotIn('path', result)

    @mock.patch('pkg_resources.get_distribution')
    def test_pkg_info_for_wrong_dist_version(self, get_distribution_mock):
        get_distribution_mock.side_effect = pkg_resources.VersionConflict

        result = deps.pkg_info()

        self.assertEquals('Mopidy', result['name'])
        self.assertNotIn('version', result)
        self.assertNotIn('path', result)
