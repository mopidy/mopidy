from subprocess import Popen, PIPE

from mopidy.mixers import BaseMixer

class OsaMixer(BaseMixer):
    def _get_volume(self):
        try:
            return int(Popen(
                ['osascript', '-e', 'output volume of (get volume settings)'],
                stdout=PIPE).communicate()[0])
        except ValueError:
            return None

    def _set_volume(self, volume):
        Popen(['osascript', '-e', 'set volume output volume %d' % volume])
