# encoding: utf-8

from __future__ import unicode_literals

from mopidy import settings
from mock import patch
from tests import unittest
from mopidy.backends.soundcloud import soundcloud

class SoundCloudClientTest(unittest.TestCase):

    def setUp(self):
        settings.SOUNDCLOUD_AUTH_TOKEN = '1-11-1111'
        with patch.object(soundcloud.SoundCloudClient, '_get') as get:
            get.return_value.status_code = 200
            get.return_value.content = {'username': 'mopidy', 'user_id': 1}
            super(LocalPlaybackControllerTest, self).setUp()

    def tearDown(self):
        settings.runtime.clear()

    def test_explore_returns_empty(self):

        "create_explore_playlist should return empty tracks,\
         when streamable is False"
