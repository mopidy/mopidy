import asyncore
import logging
import logging.handlers
import multiprocessing
import optparse
import os
import sys

sys.path.insert(0,
    os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

from mopidy import get_version, settings, SettingsError
from mopidy.process import CoreProcess
from mopidy.utils import get_class
from mopidy.utils.path import get_or_create_folder

logger = logging.getLogger('mopidy.main')

def main():
    options = _parse_options()
    _setup_logging(options.verbosity_level, options.dump)
    logger.info('-- Starting Mopidy --')
    get_or_create_folder('~/.mopidy/')
    core_queue = multiprocessing.Queue()
    get_class(settings.SERVER)(core_queue).start()
    output_class = get_class(settings.OUTPUT)
    backend_class = get_class(settings.BACKENDS[0])
    frontend_class = get_class(settings.FRONTEND)
    core = CoreProcess(core_queue, output_class, backend_class, frontend_class)
    core.start()
    asyncore.loop()

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
    return parser.parse_args()[0]

def _setup_logging(verbosity_level, dump):
    _setup_console_logging(verbosity_level)
    if dump:
        _setup_dump_logging()

def _setup_console_logging(verbosity_level):
    if verbosity_level == 0:
        level = logging.WARNING
    elif verbosity_level == 2:
        level = logging.DEBUG
    else:
        level = logging.INFO
    logging.basicConfig(format=settings.CONSOLE_LOG_FORMAT, level=level)

def _setup_dump_logging():
    root = logging.getLogger('')
    root.setLevel(logging.DEBUG)
    formatter = logging.Formatter(settings.DUMP_LOG_FORMAT)
    handler = logging.handlers.RotatingFileHandler(
        settings.DUMP_LOG_FILENAME, maxBytes=102400, backupCount=3)
    handler.setFormatter(formatter)
    root.addHandler(handler)

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
