import logging
import multiprocessing

from mopidy import settings
from mopidy.utils import get_class
from mopidy.utils.process import BaseProcess, unpickle_connection

logger = logging.getLogger('mopidy.core')

class CoreProcess(BaseProcess):
    def __init__(self, options):
        super(CoreProcess, self).__init__(name='CoreProcess')
        self.options = options
        self.core_queue = multiprocessing.Queue()
        self.output_queue = None
        self.backend = None
        self.dispatcher = None

    def run_inside_try(self):
        self.setup()
        while True:
            message = self.core_queue.get()
            self.process_message(message)

    def setup(self):
        self.setup_output()
        self.setup_backend()
        self.setup_frontend()

    def setup_output(self):
        self.output_queue = multiprocessing.Queue()
        get_class(settings.OUTPUT)(self.core_queue, self.output_queue)

    def setup_backend(self):
        self.backend = get_class(settings.BACKENDS[0])(
            self.core_queue, self.output_queue)

    def setup_frontend(self):
        frontend = get_class(settings.FRONTENDS[0])()
        frontend.start_server(self.core_queue)
        self.dispatcher = frontend.create_dispatcher(self.backend)

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
