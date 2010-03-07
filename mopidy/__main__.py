import asyncore
import logging
import os
import sys

sys.path.insert(0,
    os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

from mopidy import settings
from mopidy.exceptions import SettingError
from mopidy.mpd.server import MpdServer

logger = logging.getLogger('mopidy')

def main():
    _setup_logging(2)
    mixer = _get_class(settings.MIXER)()
    backend = _get_class(settings.BACKENDS[0])(mixer=mixer)
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

def _get_class(name):
    module_name = name[:name.rindex('.')]
    class_name = name[name.rindex('.') + 1:]
    logger.info('Loading: %s from %s', class_name, module_name)
    module = __import__(module_name, globals(), locals(), [class_name], -1)
    class_object = getattr(module, class_name)
    return class_object

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        sys.exit('\nInterrupted by user')
    except SettingError, e:
        sys.exit('%s' % e)
