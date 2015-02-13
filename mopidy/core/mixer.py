from __future__ import absolute_import, unicode_literals

import logging


logger = logging.getLogger(__name__)


class MixerController(object):
    pykka_traversable = True

    def __init__(self, mixer):
        self._mixer = mixer
        self._volume = None
        self._mute = False

    def get_volume(self):
        """Get the volume.

        Integer in range [0..100] or :class:`None` if unknown.

        The volume scale is linear.
        """
        if self._mixer is not None:
            return self._mixer.get_volume().get()

    def set_volume(self, volume):
        """Set the volume.

        The volume is defined as an integer in range [0..100].

        The volume scale is linear.
        """
        if self._mixer is not None:
            self._mixer.set_volume(volume)

    def get_mute(self):
        """Get mute state.

        :class:`True` if muted, :class:`False` unmuted, :class:`None` if
        unknown.
        """
        if self._mixer is not None:
            return self._mixer.get_mute().get()

    def set_mute(self, mute):
        """Set mute state.

        :class:`True` to mute, :class:`False` to unmute.
        """
        if self._mixer is not None:
            self._mixer.set_mute(bool(mute))
