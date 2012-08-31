import pygst
pygst.require('0.10')
import gst

import pykka
import pylast
import spotify

from mopidy.utils import deps

from tests import unittest


class DepsTest(unittest.TestCase):
    def test_format_dependency_list(self):
        adapters = [
            lambda: dict(name='Python', version='FooPython 2.7.3'),
            lambda: dict(name='Platform', version='Loonix 4.0.1'),
            lambda: dict(name='Pykka', path='/foo/bar/baz.py', other='Quux')
        ]

        result = deps.format_dependency_list(adapters)

        self.assertIn('Python: FooPython 2.7.3', result)
        self.assertIn('Platform: Loonix 4.0.1', result)
        self.assertIn('Pykka: not found', result)
        self.assertIn('Imported from: /foo/bar', result)
        self.assertNotIn('/baz.py', result)
        self.assertIn('Quux', result)

    def test_gstreamer_info(self):
        result = deps.gstreamer_info()

        self.assertEquals('Gstreamer', result['name'])
        self.assertEquals('.'.join(map(str, gst.get_gst_version())), result['version'])
        self.assertIn('gst', result['path'])
        self.assertIn('Python wrapper: gst-python', result['other'])
        self.assertIn('.'.join(map(str, gst.get_pygst_version())), result['other'])

    def test_pykka_info(self):
        result = deps.pykka_info()

        self.assertEquals('Pykka', result['name'])
        self.assertEquals(pykka.__version__, result['version'])
        self.assertIn('pykka', result['path'])

    def test_pyspotify_info(self):
        result = deps.pyspotify_info()

        self.assertEquals('pyspotify', result['name'])
        self.assertEquals(spotify.__version__, result['version'])
        self.assertIn('spotify', result['path'])
        self.assertIn('Built for libspotify API version', result['other'])
        self.assertIn(str(spotify.api_version), result['other'])

    def test_pylast_info(self):
        result = deps.pylast_info()

        self.assertEquals('pylast', result['name'])
        self.assertEquals(pylast.__version__, result['version'])
        self.assertIn('pylast', result['path'])
