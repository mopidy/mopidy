import alsaaudio
import logging

from mopidy.mixers import BaseMixer

logger = logging.getLogger('mopidy.mixers.alsa')

class AlsaMixer(BaseMixer):
    """
    Mixer which uses the Advanced Linux Sound Architecture (ALSA) to control
    volume.
    """

    def __init__(self, *args, **kwargs):
        super(AlsaMixer, self).__init__(*args, **kwargs)
        # A mixer named 'Master' does not always exist, so we fall back to
        # using 'PCM'. If this turns out to be a bad solution, we should make
        # it possible to override with a setting.
        self._mixer = None
        for mixer_name in (u'Master', u'PCM'):
            if mixer_name in alsaaudio.mixers():
                logger.info(u'Mixer in use: %s', mixer_name)
                self._mixer = alsaaudio.Mixer(mixer_name)
                break
        assert self._mixer is not None

    def _get_volume(self):
        return self._mixer.getvolume()[0]

    def _set_volume(self, volume):
        self._mixer.setvolume(volume)
