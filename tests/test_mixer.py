from __future__ import absolute_import, unicode_literals

import unittest

import mock

from mopidy import mixer


class MixerListenerTest(unittest.TestCase):

    def setUp(self):  # noqa: N802
        self.listener = mixer.MixerListener()

    def test_on_event_forwards_to_specific_handler(self):
        self.listener.volume_changed = mock.Mock()

        self.listener.on_event(
            'volume_changed', volume=60)

        self.listener.volume_changed.assert_called_with(volume=60)

    def test_listener_has_default_impl_for_volume_changed(self):
        self.listener.volume_changed(volume=60)

    def test_listener_has_default_impl_for_mute_changed(self):
        self.listener.mute_changed(mute=True)
