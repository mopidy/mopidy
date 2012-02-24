import logging

from mopidy import listeners, settings

logger = logging.getLogger('mopidy.mixers')

class BaseMixer(object):
    """
    **Settings:**

    - :attr:`mopidy.settings.MIXER_MAX_VOLUME`
    """

    amplification_factor = settings.MIXER_MAX_VOLUME / 100.0

    @property
    def volume(self):
        """
        The audio volume

        Integer in range [0, 100]. :class:`None` if unknown. Values below 0 is
        equal to 0. Values above 100 is equal to 100.
        """
        if not hasattr(self, '_user_volume'):
            self._user_volume = 0
        volume = self.get_volume()
        if volume is None or not self.amplification_factor < 1:
            return volume
        else:
            user_volume = int(volume / self.amplification_factor)
            if (user_volume - 1) <= self._user_volume <= (user_volume + 1):
                return self._user_volume
            else:
                return user_volume

    @volume.setter
    def volume(self, volume):
        if not hasattr(self, '_user_volume'):
            self._user_volume = 0
        volume = int(volume)
        if volume < 0:
            volume = 0
        elif volume > 100:
            volume = 100
        self._user_volume = volume
        real_volume = int(volume * self.amplification_factor)
        self.set_volume(real_volume)
        self._trigger_volume_changed()

    def get_volume(self):
        """
        Return volume as integer in range [0, 100]. :class:`None` if unknown.

        *MUST be implemented by subclass.*
        """
        raise NotImplementedError

    def set_volume(self, volume):
        """
        Set volume as integer in range [0, 100].

        *MUST be implemented by subclass.*
        """
        raise NotImplementedError

    def _trigger_volume_changed(self):
        logger.debug(u'Triggering volume changed event')
        listeners.BackendListener.send('volume_changed')
