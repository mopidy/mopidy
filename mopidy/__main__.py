import asyncore
import logging
from multiprocessing import Queue
import os
import sys

sys.path.insert(0,
    os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

from mopidy import get_class, settings, SettingsError
from mopidy.core import CoreProcess
from mopidy.mpd.server import MpdServer

logger = logging.getLogger('mopidy')

def main():
    _setup_logging(2)

    # multiprocessing branch plan
    # ---------------------------
    #
    # TODO Init MpdServer in MainThread or in new Process?

    main_queue = Queue()
    core_queue = Queue()
    server_queue = Queue()
    core = CoreProcess(core_queue=core_queue,
        main_queue=main_queue, server_queue=server_queue)
    core.start()
    while True:
        message = main_queue.get()
        if message['command'] == 'core_ready':
            MpdServer(core_queue=core_queue)
            asyncore.loop()
        else:
            logger.warning(u'Cannot handle message: %s', message)

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
