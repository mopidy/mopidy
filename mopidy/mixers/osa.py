from subprocess import Popen, PIPE
import time

from pykka.actor import ThreadingActor

from mopidy.mixers.base import BaseMixer

class OsaMixer(ThreadingActor, BaseMixer):
    """
    Mixer which uses ``osascript`` on OS X to control volume.

    **Dependencies:**

    - None

    **Settings:**

    - None
    """

    CACHE_TTL = 30

    _cache = None
    _last_update = None

    def _valid_cache(self):
        return (self._cache is not None
            and self._last_update is not None
            and (int(time.time() - self._last_update) < self.CACHE_TTL))

    def get_volume(self):
        if not self._valid_cache():
            try:
                self._cache = int(Popen(
                    ['osascript', '-e',
                        'output volume of (get volume settings)'],
                    stdout=PIPE).communicate()[0])
            except ValueError:
                self._cache = None
            self._last_update = int(time.time())
        return self._cache

    def set_volume(self, volume):
        Popen(['osascript', '-e', 'set volume output volume %d' % volume])
        self._cache = volume
        self._last_update = int(time.time())
