from __future__ import absolute_import, unicode_literals

import logging

from mopidy.utils import validation


logger = logging.getLogger(__name__)


class MixerController(object):
    pykka_traversable = True

    def __init__(self, mixer):
        self._mixer = mixer

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

        Returns :class:`True` if call is successful, otherwise :class:`False`.
        """
        validation.check_integer(volume, min=0, max=100)

        if self._mixer is None:
            return False
        else:
            return self._mixer.set_volume(volume).get()

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

        Returns :class:`True` if call is successful, otherwise :class:`False`.
        """
        validation.check_boolean(mute)
        if self._mixer is None:
            return False
        else:
            return self._mixer.set_mute(bool(mute)).get()
