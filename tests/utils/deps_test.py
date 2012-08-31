import pykka

from mopidy.utils import deps

from tests import unittest


class DepsTest(unittest.TestCase):
    def test_format_dependency_list(self):
        adapters = [
            lambda: dict(name='Python', version='FooPython 2.7.3'),
            lambda: dict(name='Platform', version='Loonix 4.0.1'),
            lambda: dict(name='Pykka', version='0.1337', path='/foo/bar/baz')
        ]

        result = deps.format_dependency_list(adapters)

        self.assertIn('Python: FooPython 2.7.3', result)
        self.assertIn('Platform: Loonix 4.0.1', result)
        self.assertIn('Imported from: /foo/bar/baz', result)

    def test_pykka_info(self):
        result = deps.pykka_info()

        self.assertEquals('Pykka', result['name'])
        self.assertEquals(pykka.__version__, result['version'])
        self.assertIn('pykka', result['path'])
