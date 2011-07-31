import os

from mopidy import settings as default_settings_module, SettingsError
from mopidy.utils.settings import (format_settings_list, mask_value_if_secret,
    SettingsProxy, validate_settings)

from tests import unittest


class ValidateSettingsTest(unittest.TestCase):
    def setUp(self):
        self.defaults = {
            'MPD_SERVER_HOSTNAME': '::',
            'MPD_SERVER_PORT': 6600,
            'SPOTIFY_BITRATE': 160,
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

    def test_unavailable_bitrate_setting_returns_error(self):
        result = validate_settings(self.defaults,
            {'SPOTIFY_BITRATE': 50})
        self.assertEqual(result['SPOTIFY_BITRATE'],
            u'Unavailable Spotify bitrate. ' +
            u'Available bitrates are 96, 160, and 320.')

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
        self.settings.local.clear()

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

    def test_value_ending_in_file_can_be_none(self):
        self.settings.TEST_FILE = None
        self.assertEqual(self.settings.TEST_FILE, None)

    def test_value_ending_in_path_can_be_none(self):
        self.settings.TEST_PATH = None
        self.assertEqual(self.settings.TEST_PATH, None)

    def test_interactive_input_of_missing_defaults(self):
        self.settings.default['TEST'] = ''
        interactive_input = 'input'
        self.settings._read_from_stdin = lambda _: interactive_input
        self.settings.validate(interactive=True)
        self.assertEqual(interactive_input, self.settings.TEST)

    def test_interactive_input_not_needed_when_setting_is_set_locally(self):
        self.settings.default['TEST'] = ''
        self.settings.local['TEST'] = 'test'
        self.settings._read_from_stdin = lambda _: self.fail(
            'Should not read from stdin')
        self.settings.validate(interactive=True)


class FormatSettingListTest(unittest.TestCase):
    def setUp(self):
        self.settings = SettingsProxy(default_settings_module)

    def test_contains_the_setting_name(self):
        self.settings.TEST = u'test'
        result = format_settings_list(self.settings)
        self.assert_('TEST:' in result, result)

    def test_repr_of_a_string_value(self):
        self.settings.TEST = u'test'
        result = format_settings_list(self.settings)
        self.assert_("TEST: u'test'" in result, result)

    def test_repr_of_an_int_value(self):
        self.settings.TEST = 123
        result = format_settings_list(self.settings)
        self.assert_("TEST: 123" in result, result)

    def test_repr_of_a_tuple_value(self):
        self.settings.TEST = (123, u'abc')
        result = format_settings_list(self.settings)
        self.assert_("TEST: (123, u'abc')" in result, result)

    def test_passwords_are_masked(self):
        self.settings.TEST_PASSWORD = u'secret'
        result = format_settings_list(self.settings)
        self.assert_("TEST_PASSWORD: u'secret'" not in result, result)
        self.assert_("TEST_PASSWORD: u'********'" in result, result)

    def test_short_values_are_not_pretty_printed(self):
        self.settings.FRONTEND = (u'mopidy.frontends.mpd.MpdFrontend',)
        result = format_settings_list(self.settings)
        self.assert_("FRONTEND: (u'mopidy.frontends.mpd.MpdFrontend',)" in result,
            result)

    def test_long_values_are_pretty_printed(self):
        self.settings.FRONTEND = (u'mopidy.frontends.mpd.MpdFrontend',
            u'mopidy.frontends.lastfm.LastfmFrontend')
        result = format_settings_list(self.settings)
        self.assert_("""FRONTEND: 
  (u'mopidy.frontends.mpd.MpdFrontend',
   u'mopidy.frontends.lastfm.LastfmFrontend')""" in result, result)
