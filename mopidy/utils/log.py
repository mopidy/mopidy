from __future__ import unicode_literals

import logging
import logging.handlers

from . import deps, versioning


def setup_logging(config, verbosity_level, save_debug_log):
    setup_root_logger()
    setup_console_logging(config, verbosity_level)
    if save_debug_log:
        setup_debug_logging_to_file(config)
    if hasattr(logging, 'captureWarnings'):
        # New in Python 2.7
        logging.captureWarnings(True)

    logger = logging.getLogger('mopidy.utils.log')
    logger.info('Starting Mopidy %s', versioning.get_version())
    logger.info('%(name)s: %(version)s', deps.platform_info())
    logger.info('%(name)s: %(version)s', deps.python_info())


def setup_log_levels(config):
    for name, level in config['logging.levels'].items():
        logging.getLogger(name).setLevel(level)


def setup_root_logger():
    root = logging.getLogger('')
    root.setLevel(logging.DEBUG)


def setup_console_logging(config, verbosity_level):
    if verbosity_level == 0:
        log_level = logging.WARNING
        log_format = config['logging']['console_format']
    elif verbosity_level >= 2:
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
