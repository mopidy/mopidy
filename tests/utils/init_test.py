from mopidy import utils

from tests import unittest


class GetClassTest(unittest.TestCase):
    def test_loading_module_that_does_not_exist(self):
        with self.assertRaises(ImportError):
            utils.get_class('foo.bar.Baz')

    def test_loading_class_that_does_not_exist(self):
        with self.assertRaises(ImportError):
            utils.get_class('unittest.FooBarBaz')

    def test_loading_incorrect_class_path(self):
        with self.assertRaises(ImportError):
            utils.get_class('foobarbaz')

    def test_import_error_message_contains_complete_class_path(self):
        try:
            utils.get_class('foo.bar.Baz')
        except ImportError as e:
            self.assertIn('foo.bar.Baz', str(e))

    def test_loading_existing_class(self):
        cls = utils.get_class('unittest.TestCase')
        self.assertEqual(cls.__name__, 'TestCase')
