import os
import unittest

from mopidy import settings as default_settings_module, SettingsError
from mopidy.utils.settings import validate_settings, SettingsProxy
from mopidy.utils.settings import mask_value_if_secret

class ValidateSettingsTest(unittest.TestCase):
    def setUp(self):
        self.defaults = {
            'MPD_SERVER_HOSTNAME': '::',
            'MPD_SERVER_PORT': 6600,
        }

    def test_no_errors_yields_empty_dict(self):
        result = validate_settings(self.defaults, {})
        self.assertEqual(result, {})

    def test_unknown_setting_returns_error(self):
        result = validate_settings(self.defaults,
            {'MPD_SERVER_HOSTNMAE': '127.0.0.1'})
        self.assertEqual(result['MPD_SERVER_HOSTNMAE'],
            u'Unknown setting. Is it misspelled?')

    def test_not_renamed_setting_returns_error(self):
        result = validate_settings(self.defaults,
            {'SERVER_HOSTNAME': '127.0.0.1'})
        self.assertEqual(result['SERVER_HOSTNAME'],
            u'Deprecated setting. Use MPD_SERVER_HOSTNAME.')

    def test_unneeded_settings_returns_error(self):
        result = validate_settings(self.defaults,
            {'SPOTIFY_LIB_APPKEY': '/tmp/foo'})
        self.assertEqual(result['SPOTIFY_LIB_APPKEY'],
            u'Deprecated setting. It may be removed.')

    def test_deprecated_setting_value_returns_error(self):
        result = validate_settings(self.defaults,
            {'BACKENDS': ('mopidy.backends.despotify.DespotifyBackend',)})
        self.assertEqual(result['BACKENDS'],
            u'Deprecated setting value. ' +
            '"mopidy.backends.despotify.DespotifyBackend" is no longer ' +
            'available.')

    def test_two_errors_are_both_reported(self):
        result = validate_settings(self.defaults,
            {'FOO': '', 'BAR': ''})
        self.assertEqual(len(result), 2)

    def test_masks_value_if_secret(self):
        secret = mask_value_if_secret('SPOTIFY_PASSWORD', 'bar')
        self.assertEqual(u'********', secret)

    def test_does_not_mask_value_if_not_secret(self):
        not_secret = mask_value_if_secret('SPOTIFY_USERNAME', 'foo')
        self.assertEqual('foo', not_secret)

    def test_does_not_mask_value_if_none(self):
        not_secret = mask_value_if_secret('SPOTIFY_USERNAME', None)
        self.assertEqual(None, not_secret)


class SettingsProxyTest(unittest.TestCase):
    def setUp(self):
        self.settings = SettingsProxy(default_settings_module)

    def test_set_and_get_attr(self):
        self.settings.TEST = 'test'
        self.assertEqual(self.settings.TEST, 'test')

    def test_getattr_raises_error_on_missing_setting(self):
        try:
            _ = self.settings.TEST
            self.fail(u'Should raise exception')
        except SettingsError as e:
            self.assertEqual(u'Setting "TEST" is not set.', e.message)

    def test_getattr_raises_error_on_empty_setting(self):
        self.settings.TEST = u''
        try:
            _ = self.settings.TEST
            self.fail(u'Should raise exception')
        except SettingsError as e:
            self.assertEqual(u'Setting "TEST" is empty.', e.message)

    def test_getattr_does_not_raise_error_if_setting_is_false(self):
        self.settings.TEST = False
        self.assertEqual(False, self.settings.TEST)

    def test_getattr_does_not_raise_error_if_setting_is_none(self):
        self.settings.TEST = None
        self.assertEqual(None, self.settings.TEST)

    def test_getattr_does_not_raise_error_if_setting_is_zero(self):
        self.settings.TEST = 0
        self.assertEqual(0, self.settings.TEST)

    def test_setattr_updates_runtime_settings(self):
        self.settings.TEST = 'test'
        self.assert_('TEST' in self.settings.runtime)

    def test_setattr_updates_runtime_with_value(self):
        self.settings.TEST = 'test'
        self.assertEqual(self.settings.runtime['TEST'], 'test')

    def test_runtime_value_included_in_current(self):
        self.settings.TEST = 'test'
        self.assertEqual(self.settings.current['TEST'], 'test')

    def test_value_ending_in_path_is_expanded(self):
        self.settings.TEST_PATH = '~/test'
        actual = self.settings.TEST_PATH
        expected = os.path.expanduser('~/test')
        self.assertEqual(actual, expected)

    def test_value_ending_in_path_is_absolute(self):
        self.settings.TEST_PATH = './test'
        actual = self.settings.TEST_PATH
        expected = os.path.abspath('./test')
        self.assertEqual(actual, expected)

    def test_value_ending_in_file_is_expanded(self):
        self.settings.TEST_FILE = '~/test'
        actual = self.settings.TEST_FILE
        expected = os.path.expanduser('~/test')
        self.assertEqual(actual, expected)

    def test_value_ending_in_file_is_absolute(self):
        self.settings.TEST_FILE = './test'
        actual = self.settings.TEST_FILE
        expected = os.path.abspath('./test')
        self.assertEqual(actual, expected)

    def test_value_not_ending_in_path_or_file_is_not_expanded(self):
        self.settings.TEST = '~/test'
        actual = self.settings.TEST
        self.assertEqual(actual, '~/test')

    def test_value_not_ending_in_path_or_file_is_not_absolute(self):
        self.settings.TEST = './test'
        actual = self.settings.TEST
        self.assertEqual(actual, './test')
