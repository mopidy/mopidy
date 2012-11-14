from __future__ import unicode_literals

import logging
import logging.handlers

from mopidy import settings
from . import deps, versioning


def setup_logging(verbosity_level, save_debug_log):
    setup_root_logger()
    setup_console_logging(verbosity_level)
    if save_debug_log:
        setup_debug_logging_to_file()
    if hasattr(logging, 'captureWarnings'):
        # New in Python 2.7
        logging.captureWarnings(True)
    logger = logging.getLogger('mopidy.utils.log')
    logger.info('Starting Mopidy %s', versioning.get_version())
    logger.info('%(name)s: %(version)s', deps.platform_info())
    logger.info('%(name)s: %(version)s', deps.python_info())


def setup_root_logger():
    root = logging.getLogger('')
    root.setLevel(logging.DEBUG)


def setup_console_logging(verbosity_level):
    if verbosity_level == 0:
        log_level = logging.WARNING
        log_format = settings.CONSOLE_LOG_FORMAT
    elif verbosity_level >= 2:
        log_level = logging.DEBUG
        log_format = settings.DEBUG_LOG_FORMAT
    else:
        log_level = logging.INFO
        log_format = settings.CONSOLE_LOG_FORMAT
    formatter = logging.Formatter(log_format)
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    handler.setLevel(log_level)
    root = logging.getLogger('')
    root.addHandler(handler)

    if verbosity_level < 3:
        logging.getLogger('pykka').setLevel(logging.INFO)

    if verbosity_level < 2:
        logging.getLogger('cherrypy').setLevel(logging.WARNING)


def setup_debug_logging_to_file():
    formatter = logging.Formatter(settings.DEBUG_LOG_FORMAT)
    handler = logging.handlers.RotatingFileHandler(
        settings.DEBUG_LOG_FILENAME, maxBytes=10485760, backupCount=3)
    handler.setFormatter(formatter)
    handler.setLevel(logging.DEBUG)
    root = logging.getLogger('')
    root.addHandler(handler)
