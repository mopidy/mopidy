class BaseMixer(object):
    @property
    def volume(self):
        """
        The audio volume

        Integer in range [0, 100]. :class:`None` if unknown. Values below 0 is
        equal to 0. Values above 100 is equal to 100.
        """
        return self._get_volume()

    @volume.setter
    def volume(self, volume):
        volume = int(volume)
        if volume < 0:
            volume = 0
        elif volume > 100:
            volume = 100
        self._set_volume(volume)

    def _get_volume(self):
        """
        Return volume as integer in range [0, 100]. :class:`None` if unknown.

        *Must be implemented by subclass.*
        """
        raise NotImplementedError

    def _set_volume(self, volume):
        """
        Set volume as integer in range [0, 100].

        *Must be implemented by subclass.*
        """
        raise NotImplementedError
