from __future__ import unicode_literals

import logging
import logging.config
import logging.handlers


class DelayedHandler(logging.Handler):
    def __init__(self):
        logging.Handler.__init__(self)
        self._released = False
        self._buffer = []

    def handle(self, record):
        if not self._released:
            self._buffer.append(record)

    def release(self):
        self._released = True
        root = logging.getLogger('')
        while self._buffer:
            root.handle(self._buffer.pop(0))


_delayed_handler = DelayedHandler()


def bootstrap_delayed_logging():
    root = logging.getLogger('')
    root.setLevel(logging.DEBUG)
    root.addHandler(_delayed_handler)


def setup_logging(config, extensions, verbosity_level, save_debug_log):
    setup_log_levels(config)

    setup_console_logging(config, extensions, verbosity_level)

    if save_debug_log:
        setup_debug_logging_to_file(config, extensions)

    logging.captureWarnings(True)

    if config['logging']['config_file']:
        logging.config.fileConfig(config['logging']['config_file'])

    _delayed_handler.release()


def setup_log_levels(config):
    for name, level in config['loglevels'].items():
        logging.getLogger(name).setLevel(level)


LOG_LEVELS = {
    -1: dict(root=logging.ERROR, mopidy=logging.WARNING),
    0: dict(root=logging.ERROR, mopidy=logging.INFO),
    1: dict(root=logging.WARNING, mopidy=logging.DEBUG),
    2: dict(root=logging.INFO, mopidy=logging.DEBUG),
    3: dict(root=logging.DEBUG, mopidy=logging.DEBUG),
}


def setup_console_logging(config, extensions, verbosity_level):
    if verbosity_level < min(LOG_LEVELS.keys()):
        verbosity_level = min(LOG_LEVELS.keys())
    if verbosity_level > max(LOG_LEVELS.keys()):
        verbosity_level = max(LOG_LEVELS.keys())

    if verbosity_level < 1:
        log_format = config['logging']['console_format']
    else:
        log_format = config['logging']['debug_format']
    formatter = logging.Formatter(log_format)

    root_handler = logging.StreamHandler()
    root_handler.setFormatter(formatter)
    root_handler.setLevel(LOG_LEVELS[verbosity_level]['root'])
    logging.getLogger('').addHandler(root_handler)

    mopidy_handler = logging.StreamHandler()
    mopidy_handler.setFormatter(formatter)
    mopidy_handler.setLevel(LOG_LEVELS[verbosity_level]['mopidy'])
    add_mopidy_handler(extensions, mopidy_handler)


def setup_debug_logging_to_file(config, extensions):
    formatter = logging.Formatter(config['logging']['debug_format'])
    handler = logging.handlers.RotatingFileHandler(
        config['logging']['debug_file'], maxBytes=10485760, backupCount=3)
    handler.setFormatter(formatter)

    logging.getLogger('').addHandler(handler)

    # We must add our handler explicitly, since the mopidy* handlers don't
    # propagate to the root handler.
    add_mopidy_handler(extensions, handler)


def add_mopidy_handler(extensions, handler):
    names = ['mopidy_%s' % ext.ext_name for ext in extensions]
    names.append('mopidy')
    for name in names:
        logger = logging.getLogger(name)
        logger.propagate = False
        logger.addHandler(handler)
