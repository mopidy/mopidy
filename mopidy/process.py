import logging
import multiprocessing
from multiprocessing.reduction import reduce_connection
import pickle
import sys

from mopidy import SettingsError

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
        except ImportError as e:
            logger.error(e)
            sys.exit(1)

    def run_inside_try(self):
        raise NotImplementedError


class CoreProcess(BaseProcess):
    def __init__(self, core_queue, output_class, backend_class, frontend):
        super(CoreProcess, self).__init__()
        self.core_queue = core_queue
        self.output_queue = None
        self.output_class = output_class
        self.backend_class = backend_class
        self.output = None
        self.backend = None
        self.frontend = frontend
        self.dispatcher = None

    def run_inside_try(self):
        self.setup()
        while True:
            message = self.core_queue.get()
            self.process_message(message)

    def setup(self):
        self.output_queue = multiprocessing.Queue()
        self.output = self.output_class(self.core_queue, self.output_queue)
        self.backend = self.backend_class(self.core_queue, self.output_queue)
        self.dispatcher = self.frontend.create_dispatcher(self.backend)

    def process_message(self, message):
        if message.get('to') == 'output':
            self.output_queue.put(message)
        elif message['command'] == 'mpd_request':
            response = self.dispatcher.handle_request(message['request'])
            connection = unpickle_connection(message['reply_to'])
            connection.send(response)
        elif message['command'] == 'end_of_track':
            self.backend.playback.on_end_of_track()
        elif message['command'] == 'stop_playback':
            self.backend.playback.stop()
        elif message['command'] == 'set_stored_playlists':
            self.backend.stored_playlists.playlists = message['playlists']
        else:
            logger.warning(u'Cannot handle message: %s', message)
