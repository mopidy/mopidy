import logging
import multiprocessing

from mopidy import settings
from mopidy.utils import get_class
from mopidy.utils.process import BaseProcess, unpickle_connection

logger = logging.getLogger('mopidy.core')

class CoreProcess(BaseProcess):
    def __init__(self):
        super(CoreProcess, self).__init__(name='CoreProcess')
        self.core_queue = multiprocessing.Queue()
        self.output_queue = None
        self.backend = None
        self.frontend = None

    def run_inside_try(self):
        self.setup()
        while True:
            message = self.core_queue.get()
            self.process_message(message)

    def setup(self):
        self.output_queue = self.setup_output(self.core_queue)
        self.backend = self.setup_backend(self.core_queue, self.output_queue)
        self.frontend = self.setup_frontend(self.core_queue, self.backend)

    def setup_output(self, core_queue):
        output_queue = multiprocessing.Queue()
        get_class(settings.OUTPUT)(core_queue, output_queue)
        return output_queue

    def setup_backend(self, core_queue, output_queue):
        return get_class(settings.BACKENDS[0])(core_queue, output_queue)

    def setup_frontend(self, core_queue, backend):
        frontend = get_class(settings.FRONTENDS[0])()
        frontend.start_server(core_queue)
        frontend.create_dispatcher(backend)
        return frontend

    def process_message(self, message):
        if message.get('to') == 'output':
            self.output_queue.put(message)
        elif message['command'] == 'mpd_request':
            response = self.frontend.dispatcher.handle_request(message['request'])
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
