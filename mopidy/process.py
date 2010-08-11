import logging
import multiprocessing
from multiprocessing.reduction import reduce_connection
import pickle
import sys

from mopidy import settings, SettingsError
from mopidy.utils import get_class

logger = logging.getLogger('mopidy.process')

def pickle_connection(connection):
    return pickle.dumps(reduce_connection(connection))

def unpickle_connection(pickled_connection):
    # From http://stackoverflow.com/questions/1446004
    (func, args) = pickle.loads(pickled_connection)
    return func(*args)


class BaseProcess(multiprocessing.Process):
    def run(self):
        try:
            self.run_inside_try()
        except KeyboardInterrupt:
            logger.info(u'Interrupted by user')
            sys.exit(0)
        except SettingsError as e:
            logger.error(e.message)
            sys.exit(1)

    def run_inside_try(self):
        raise NotImplementedError


class CoreProcess(BaseProcess):
    def __init__(self, core_queue):
        super(CoreProcess, self).__init__()
        self.core_queue = core_queue
        self.output_connection = None
        self.output = None
        self.backend = None
        self.frontend = None

    def run_inside_try(self):
        self.setup()
        while True:
            message = self.core_queue.get()
            self.process_message(message)

    def setup(self):
        (recv_end, self.output_connection) = multiprocessing.Pipe(False)
        self.output = get_class(settings.OUTPUT)(self.core_queue, recv_end)
        self.backend = get_class(settings.BACKENDS[0])(self.core_queue)
        self.frontend = get_class(settings.FRONTEND)(self.backend)

    def process_message(self, message):
        if message.get('to') == 'output':
            self.output_connection.send(message)
        elif message['command'] == 'mpd_request':
            response = self.frontend.handle_request(message['request'])
            connection = unpickle_connection(message['reply_to'])
            connection.send(response)
        elif message['command'] == 'end_of_track':
            self.backend.playback.end_of_track_callback()
        elif message['command'] == 'stop_playback':
            self.backend.playback.stop()
        elif message['command'] == 'set_stored_playlists':
            self.backend.stored_playlists.playlists = message['playlists']
        else:
            logger.warning(u'Cannot handle message: %s', message)
