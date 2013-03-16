# encoding: utf-8

from __future__ import unicode_literals

from mock import patch
from tests import unittest
from mopidy.backends.soundcloud import soundcloud


class SoundcloudClientTest(unittest.TestCase):

    def setUp(self):
        with patch.object(soundcloud.SoundCloudClient, '_get') as get:
            get.return_value.status_code = 200
            get.return_value.content = {'username': 'mopidy', 'user_id': 1}
            self.SCC = soundcloud.SoundCloudClient('1-11-1111')

    def test_get_user(self):

        "get_user should return username mopidy"

        with patch.object(soundcloud.SoundCloudClient, '_get') as get:
            get.return_value = {'username': 'mopidy', 'user_id': 1}
            self.assertEqual(self.SCC.get_user().get('username'), 'mopidy')

    def test_return_none_no_data(self):

        "parse_track should return None if data is empty"

        self.assertEqual(self.SCC.parse_track(None), None)

    def test_return_none_if_not_track(self):

        "parse_track should return None if data is not track or not streamable"

        payload = {'kind': 'playlist', 'streamable': False}
        self.assertEqual(self.SCC.parse_track(payload), None)

    def test_sanitize_tracks(self):

        "sanitize_tracks should return only valid data"

        payload = ["Track A", None, "Track B"]
        result = ["Track A", "Track B"]
        self.assertEqual(self.SCC.sanitize_tracks(payload), result)
