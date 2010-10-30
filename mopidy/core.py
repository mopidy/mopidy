import logging
import multiprocessing
import optparse
import sys

from mopidy import get_version, settings, OptionalDependencyError
from mopidy.utils import get_class
from mopidy.utils.log import setup_logging
from mopidy.utils.path import get_or_create_folder, get_or_create_file
from mopidy.utils.process import BaseThread, GObjectEventThread
from mopidy.utils.settings import list_settings_optparse_callback

logger = logging.getLogger('mopidy.core')

class CoreProcess(BaseThread):
    def __init__(self):
        self.core_queue = multiprocessing.Queue()
        super(CoreProcess, self).__init__(self.core_queue)
        self.name = 'CoreProcess'
        self.options = self.parse_options()
        self.output = None
        self.backend = None
        self.frontends = []

    def parse_options(self):
        parser = optparse.OptionParser(version='Mopidy %s' % get_version())
        parser.add_option('-q', '--quiet',
            action='store_const', const=0, dest='verbosity_level',
            help='less output (warning level)')
        parser.add_option('-v', '--verbose',
            action='store_const', const=2, dest='verbosity_level',
            help='more output (debug level)')
        parser.add_option('--save-debug-log',
            action='store_true', dest='save_debug_log',
            help='save debug log to "./mopidy.log"')
        parser.add_option('--list-settings',
            action='callback', callback=list_settings_optparse_callback,
            help='list current settings')
        return parser.parse_args()[0]

    def run_inside_try(self):
        self.setup()
        while True:
            message = self.core_queue.get()
            self.process_message(message)

    def setup(self):
        self.setup_logging()
        self.setup_settings()
        self.gobject_loop = self.setup_gobject_loop(self.core_queue)
        self.output = self.setup_output(self.core_queue)
        self.backend = self.setup_backend(self.core_queue, self.output)
        self.frontends = self.setup_frontends(self.core_queue, self.backend)

    def setup_logging(self):
        setup_logging(self.options.verbosity_level,
            self.options.save_debug_log)
        logger.info(u'-- Starting Mopidy --')

    def setup_settings(self):
        get_or_create_folder('~/.mopidy/')
        get_or_create_file('~/.mopidy/settings.py')
        settings.validate()

    def setup_gobject_loop(self, core_queue):
        gobject_loop = GObjectEventThread(core_queue)
        gobject_loop.start()
        return gobject_loop

    def setup_output(self, core_queue):
        output = get_class(settings.OUTPUT)(core_queue)
        output.start()
        return output

    def setup_backend(self, core_queue, output):
        return get_class(settings.BACKENDS[0])(core_queue, output)

    def setup_frontends(self, core_queue, backend):
        frontends = []
        for frontend_class_name in settings.FRONTENDS:
            try:
                frontend = get_class(frontend_class_name)(core_queue, backend)
                frontend.start()
                frontends.append(frontend)
            except OptionalDependencyError as e:
                logger.info(u'Disabled: %s (%s)', frontend_class_name, e)
        return frontends

    def process_message(self, message):
        if message.get('to') == 'core':
            self.process_message_to_core(message)
        elif message.get('to') == 'output':
            self.output.process_message(message)
        elif message.get('to') == 'frontend':
            for frontend in self.frontends:
                frontend.process_message(message)
        elif message['command'] == 'end_of_track':
            self.backend.playback.on_end_of_track()
        elif message['command'] == 'stop_playback':
            self.backend.playback.stop()
        elif message['command'] == 'set_stored_playlists':
            self.backend.stored_playlists.playlists = message['playlists']
        else:
            logger.warning(u'Cannot handle message: %s', message)

    def process_message_to_core(self, message):
        assert message['to'] == 'core', u'Message recipient must be "core".'
        if message['command'] == 'exit':
            if message.get('reason') is not None:
                logger.info(u'Exiting (%s)', message['reason'])
            sys.exit(message.get('status', 0))
        else:
            logger.warning(u'Cannot handle message: %s', message)
