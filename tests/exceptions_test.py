from __future__ import unicode_literals

from mopidy import exceptions

from tests import unittest


class ExceptionsTest(unittest.TestCase):
    def test_exception_can_include_message_string(self):
        exc = exceptions.MopidyException('foo')

        self.assertEqual(exc.message, 'foo')
        self.assertEqual(str(exc), 'foo')

    def test_settings_error_is_a_mopidy_exception(self):
        self.assert_(issubclass(
            exceptions.SettingsError, exceptions.MopidyException))

    def test_optional_dependency_error_is_a_mopidy_exception(self):
        self.assert_(issubclass(
            exceptions.OptionalDependencyError, exceptions.MopidyException))

    def test_extension_error_is_a_mopidy_exception(self):
        self.assert_(issubclass(
            exceptions.ExtensionError, exceptions.MopidyException))

    def test_config_error_is_a_mopidy_exception(self):
        self.assert_(issubclass(
            exceptions.ConfigError, exceptions.MopidyException))

    def test_config_error_provides_getitem(self):
        exception = exceptions.ConfigError(
            {'field1': 'msg1', 'field2': 'msg2'})
        self.assertEqual('msg1', exception['field1'])
        self.assertEqual('msg2', exception['field2'])
        self.assertItemsEqual(['field1', 'field2'], exception)
