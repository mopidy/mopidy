import asyncore
import logging
import os
import sys

sys.path.insert(0,
    os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

from mopidy import get_class, settings, SettingsError
from mopidy.mpd.server import MpdServer

logger = logging.getLogger('mopidy')

def main():
    _setup_logging(2)

    # multiprocessing branch plan
    # ---------------------------
    #
    # TODO Init backend in new Process (named core?)
    # TODO Init mixer from backend
    # TODO Init MpdHandler from backend/core
    # TODO Init MpdServer in MainThread or in new Process?

    mixer = get_class(settings.MIXER)()
    backend = get_class(settings.BACKENDS[0])(mixer=mixer)
    MpdServer(backend=backend)
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
