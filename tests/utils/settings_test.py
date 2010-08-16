import unittest

from mopidy.utils.settings import validate_settings

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
