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


def setup_logging(config, verbosity_level, save_debug_log):
    setup_console_logging(config, verbosity_level)
    setup_log_levels(config)

    if save_debug_log:
        setup_debug_logging_to_file(config)

    logging.captureWarnings(True)

    if config['logging']['config_file']:
        logging.config.fileConfig(config['logging']['config_file'])

    _delayed_handler.release()


def setup_log_levels(config):
    for name, level in config['loglevels'].items():
        logging.getLogger(name).setLevel(level)


def setup_console_logging(config, verbosity_level):
    if verbosity_level < 0:
        log_level = logging.WARNING
        log_format = config['logging']['console_format']
    elif verbosity_level >= 1:
        log_level = logging.DEBUG
        log_format = config['logging']['debug_format']
    else:
        log_level = logging.INFO
        log_format = config['logging']['console_format']
    formatter = logging.Formatter(log_format)
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    handler.setLevel(log_level)
    root = logging.getLogger('')
    root.addHandler(handler)


def setup_debug_logging_to_file(config):
    formatter = logging.Formatter(config['logging']['debug_format'])
    handler = logging.handlers.RotatingFileHandler(
        config['logging']['debug_file'], maxBytes=10485760, backupCount=3)
    handler.setFormatter(formatter)
    handler.setLevel(logging.DEBUG)
    root = logging.getLogger('')
    root.addHandler(handler)
