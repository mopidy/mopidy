import asyncore
import logging
import multiprocessing
import os
import sys

sys.path.insert(0,
    os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

from mopidy import get_class, settings, SettingsError
from mopidy.core import CoreProcess

logger = logging.getLogger('mopidy.main')

def main():
    _setup_logging(2)
    core_queue = multiprocessing.Queue()
    core = CoreProcess(core_queue)
    core.start()
    get_class(settings.SERVER)(core_queue=core_queue)
    asyncore.loop()

def _setup_logging(verbosity_level):
    if verbosity_level == 0:
        level = logging.WARNING
    elif verbosity_level == 2:
        level = logging.DEBUG
    else:
        level = logging.INFO
    logging.basicConfig(
        format=settings.CONSOLE_LOG_FORMAT,
        level=level,
    )

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        sys.exit('\nInterrupted by user')
    except SettingsError, e:
        sys.exit('%s' % e)
