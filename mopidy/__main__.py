import logging
import multiprocessing
import optparse
import os
import sys

sys.path.insert(0,
    os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

from mopidy import get_version, settings, SettingsError
from mopidy.core import CoreProcess
from mopidy.utils import get_class
from mopidy.utils.log import setup_logging
from mopidy.utils.path import get_or_create_folder
from mopidy.utils.settings import list_settings_optparse_callback

logger = logging.getLogger('mopidy.main')

def main():
    options = _parse_options()
    setup_logging(options.verbosity_level, options.dump)
    settings.validate()
    logger.info('-- Starting Mopidy --')
    get_or_create_folder('~/.mopidy/')
    core_queue = multiprocessing.Queue()
    output_class = get_class(settings.OUTPUT)
    backend_class = get_class(settings.BACKENDS[0])
    frontend = get_class(settings.FRONTENDS[0])()
    frontend.start_server(core_queue)
    core = CoreProcess(core_queue, output_class, backend_class, frontend)
    core.start()
    logger.debug('Main done')

def _parse_options():
    parser = optparse.OptionParser(version='Mopidy %s' % get_version())
    parser.add_option('-q', '--quiet',
        action='store_const', const=0, dest='verbosity_level',
        help='less output (warning level)')
    parser.add_option('-v', '--verbose',
        action='store_const', const=2, dest='verbosity_level',
        help='more output (debug level)')
    parser.add_option('--dump',
        action='store_true', dest='dump',
        help='dump debug log to file')
    parser.add_option('--list-settings',
        action='callback', callback=list_settings_optparse_callback,
        help='list current settings')
    return parser.parse_args()[0]

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        logger.info(u'Interrupted by user')
        sys.exit(0)
    except SettingsError, e:
        logger.error(e)
        sys.exit(1)
    except SystemExit, e:
        logger.error(e)
        sys.exit(1)
