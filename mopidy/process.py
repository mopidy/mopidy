import logging
import multiprocessing
import sys

from mopidy import settings, SettingsError
from mopidy.utils import get_class, unpickle_connection

logger = logging.getLogger('mopidy.process')

class BaseProcess(multiprocessing.Process):
    def run(self):
        try:
            self._run()
        except KeyboardInterrupt:
            logger.info(u'Interrupted by user')
            sys.exit(0)
        except SettingsError as e:
            logger.error(e.message)
            sys.exit(1)

    def _run(self):
        raise NotImplementedError


class CoreProcess(BaseProcess):
    def __init__(self, core_queue):
        super(CoreProcess, self).__init__()
        self.core_queue = core_queue
        self._backend = None
        self._frontend = None

    def _run(self):
        self._setup()
        while True:
            message = self.core_queue.get()
            self._process_message(message)

    def _setup(self):
        self._backend = get_class(settings.BACKENDS[0])(
            core_queue=self.core_queue)
        self._frontend = get_class(settings.FRONTEND)(backend=self._backend)

    def _process_message(self, message):
        if message['command'] == 'mpd_request':
            response = self._frontend.handle_request(message['request'])
            connection = unpickle_connection(message['reply_to'])
            connection.send(response)
        elif message['command'] == 'end_of_track':
            self._backend.playback.end_of_track_callback()
        elif message['command'] == 'stop_playback':
            self._backend.playback.stop()
        elif message['command'] == 'set_stored_playlists':
            self._backend.stored_playlists.playlists = message['playlists']
        else:
            logger.warning(u'Cannot handle message: %s', message)
