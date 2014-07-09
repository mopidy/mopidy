from __future__ import unicode_literals


class Mixer(object):
    """Audio mixer API

    If the mixer has problems during initialization it should raise
    :exc:`~mopidy.exceptions.MixerError` with a descriptive error message. This
    will make Mopidy print the error message and exit so that the user can fix
    the issue.
    """

    name = None
    """Name of the mixer.

    Used when configuring what mixer to use. Should match the
    :attr:`~mopidy.ext.Extension.ext_name` of the extension providing the
    mixer.
    """

    def get_volume(self):
        """
        Get volume level of the mixer.

        Example values:

        0:
            Minimum volume, usually silent.
        100:
            Max volume.
        :class:`None`:
            Volume is unknown.

        *MAY be implemented by subclass.*

        :rtype: int in range [0..100] or :class:`None`
        """
        return None

    def set_volume(self, volume):
        """
        Set volume level of the mixer.

        *MAY be implemented by subclass.*

        :param volume: Volume in the range [0..100]
        :type volume: int
        :rtype: :class:`True` if success, :class:`False` if failure
        """
        return False

    def get_mute(self):
        """
        Get mute status of the mixer.

        *MAY be implemented by subclass.*

        :rtype: :class:`True` if muted, :class:`False` if unmuted,
          :class:`None` if unknown.
        """
        return None

    def set_mute(self, muted):
        """
        Mute or unmute the mixer.

        *MAY be implemented by subclass.*

        :param muted: :class:`True` to mute, :class:`False` to unmute
        :type muted: bool
        :rtype: :class:`True` if success, :class:`False` if failure
        """
        return False
