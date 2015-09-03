from __future__ import absolute_import, unicode_literals

import logging

from mopidy import listener


logger = logging.getLogger(__name__)


class Mixer(object):

    """
    Audio mixer API

    If the mixer has problems during initialization it should raise
    :exc:`mopidy.exceptions.MixerError` with a descriptive error message. This
    will make Mopidy print the error message and exit so that the user can fix
    the issue.

    :param config: the entire Mopidy configuration
    :type config: dict
    """

    name = None
    """
    Name of the mixer.

    Used when configuring what mixer to use. Should match the
    :attr:`~mopidy.ext.Extension.ext_name` of the extension providing the
    mixer.
    """

    def __init__(self, config):
        pass

    def get_volume(self):
        """
        Get volume level of the mixer on a linear scale from 0 to 100.

        Example values:

        0:
            Minimum volume, usually silent.
        100:
            Maximum volume.
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

    def trigger_volume_changed(self, volume):
        """
        Send ``volume_changed`` event to all mixer listeners.

        This method should be called by subclasses when the volume is changed,
        either because of a call to :meth:`set_volume` or because of any
        external entity changing the volume.
        """
        logger.debug('Mixer event: volume_changed(volume=%d)', volume)
        MixerListener.send('volume_changed', volume=volume)

    def get_mute(self):
        """
        Get mute state of the mixer.

        *MAY be implemented by subclass.*

        :rtype: :class:`True` if muted, :class:`False` if unmuted,
          :class:`None` if unknown.
        """
        return None

    def set_mute(self, mute):
        """
        Mute or unmute the mixer.

        *MAY be implemented by subclass.*

        :param mute: :class:`True` to mute, :class:`False` to unmute
        :type mute: bool
        :rtype: :class:`True` if success, :class:`False` if failure
        """
        return False

    def trigger_mute_changed(self, mute):
        """
        Send ``mute_changed`` event to all mixer listeners.

        This method should be called by subclasses when the mute state is
        changed, either because of a call to :meth:`set_mute` or because of
        any external entity changing the mute state.
        """
        logger.debug('Mixer event: mute_changed(mute=%s)', mute)
        MixerListener.send('mute_changed', mute=mute)

    def ping(self):
        """Called to check if the actor is still alive."""
        return True


class MixerListener(listener.Listener):

    """
    Marker interface for recipients of events sent by the mixer actor.

    Any Pykka actor that mixes in this class will receive calls to the methods
    defined here when the corresponding events happen in the mixer actor. This
    interface is used both for looking up what actors to notify of the events,
    and for providing default implementations for those listeners that are not
    interested in all events.
    """

    @staticmethod
    def send(event, **kwargs):
        """Helper to allow calling of mixer listener events"""
        listener.send(MixerListener, event, **kwargs)

    def volume_changed(self, volume):
        """
        Called after the volume has changed.

        *MAY* be implemented by actor.

        :param volume: the new volume
        :type volume: int in range [0..100]
        """
        pass

    def mute_changed(self, mute):
        """
        Called after the mute state has changed.

        *MAY* be implemented by actor.

        :param mute: :class:`True` if muted, :class:`False` if not muted
        :type mute: bool
        """
        pass
