from mopidy.utils import get_class

from tests import unittest


class GetClassTest(unittest.TestCase):
    def test_loading_module_that_does_not_exist(self):
        self.assertRaises(ImportError, get_class, 'foo.bar.Baz')

    def test_loading_class_that_does_not_exist(self):
        self.assertRaises(ImportError, get_class, 'unittest.FooBarBaz')

    def test_loading_incorrect_class_path(self):
        self.assertRaises(ImportError, get_class, 'foobarbaz')

    def test_import_error_message_contains_complete_class_path(self):
        try:
            get_class('foo.bar.Baz')
        except ImportError as e:
            self.assert_('foo.bar.Baz' in str(e))

    def test_loading_existing_class(self):
        cls = get_class('unittest.TestCase')
        self.assertEqual(cls.__name__, 'TestCase')
