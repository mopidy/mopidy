import alsaaudio
import logging

from pykka.actor import ThreadingActor

from mopidy import settings
from mopidy.mixers.base import BaseMixer

logger = logging.getLogger('mopidy.mixers.alsa')

class AlsaMixer(ThreadingActor, BaseMixer):
    """
    Mixer which uses the Advanced Linux Sound Architecture (ALSA) to control
    volume.

    **Dependencies:**

    - pyalsaaudio >= 0.2 (python-alsaaudio on Debian/Ubuntu)

    **Settings:**

    - :attr:`mopidy.settings.MIXER_ALSA_CONTROL`
    """

    def __init__(self):
        super(AlsaMixer, self).__init__()
        self._mixer = None

    def on_start(self):
        self._mixer = alsaaudio.Mixer(self._get_mixer_control())
        assert self._mixer is not None

    def _get_mixer_control(self):
        """Returns the first mixer control candidate that is known to ALSA"""
        candidates = self._get_mixer_control_candidates()
        for control in candidates:
            if control in alsaaudio.mixers():
                logger.info(u'Mixer control in use: %s', control)
                return control
            else:
                logger.debug(u'Mixer control not found, skipping: %s', control)
        logger.warning(u'No working mixer controls found. Tried: %s',
            candidates)

    def _get_mixer_control_candidates(self):
        """
        A mixer named 'Master' does not always exist, so we fall back to using
        'PCM'. If this does not work for you, you may set
        :attr:`mopidy.settings.MIXER_ALSA_CONTROL`.
        """
        if settings.MIXER_ALSA_CONTROL:
            return [settings.MIXER_ALSA_CONTROL]
        return [u'Master', u'PCM']

    def get_volume(self):
        # FIXME does not seem to see external volume changes.
        return self._mixer.getvolume()[0]

    def set_volume(self, volume):
        self._mixer.setvolume(volume)
