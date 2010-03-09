from subprocess import Popen, PIPE
import time

from mopidy.mixers import BaseMixer

CACHE_TTL = 30

class OsaMixer(BaseMixer):
    _cache = None
    _last_update = None

    def _valid_cache(self):
        return (self._cache is not None
            and self._last_update is not None
            and (int(time.time() - self._last_update) < CACHE_TTL))

    def _get_volume(self):
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

    def _set_volume(self, volume):
        Popen(['osascript', '-e', 'set volume output volume %d' % volume])
        self._cache = volume
        self._last_update = int(time.time())
