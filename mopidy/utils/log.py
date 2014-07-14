from __future__ import unicode_literals

import logging
import logging.config
import logging.handlers
import platform


LOG_LEVELS = {
    -1: dict(root=logging.ERROR, mopidy=logging.WARNING),
    0: dict(root=logging.ERROR, mopidy=logging.INFO),
    1: dict(root=logging.WARNING, mopidy=logging.DEBUG),
    2: dict(root=logging.INFO, mopidy=logging.DEBUG),
    3: dict(root=logging.DEBUG, mopidy=logging.DEBUG),
}


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
    root.setLevel(logging.NOTSET)
    root.addHandler(_delayed_handler)


def setup_logging(config, verbosity_level, save_debug_log):
    logging.captureWarnings(True)

    if config['logging']['config_file']:
        # Logging config from file must be read before other handlers are
        # added. If not, the other handlers will have no effect.
        logging.config.fileConfig(config['logging']['config_file'])

    setup_console_logging(config, verbosity_level)
    if save_debug_log:
        setup_debug_logging_to_file(config)

    _delayed_handler.release()


def setup_console_logging(config, verbosity_level):
    if verbosity_level < min(LOG_LEVELS.keys()):
        verbosity_level = min(LOG_LEVELS.keys())
    if verbosity_level > max(LOG_LEVELS.keys()):
        verbosity_level = max(LOG_LEVELS.keys())

    loglevels = config.get('loglevels', {})
    has_debug_loglevels = any([
        level < logging.INFO for level in loglevels.values()])

    verbosity_filter = VerbosityFilter(verbosity_level, loglevels)

    if verbosity_level < 1 and not has_debug_loglevels:
        log_format = config['logging']['console_format']
    else:
        log_format = config['logging']['debug_format']
    formatter = logging.Formatter(log_format)

    if config['logging']['color']:
        handler = ColorizingStreamHandler()
    else:
        handler = logging.StreamHandler()
    handler.addFilter(verbosity_filter)
    handler.setFormatter(formatter)

    logging.getLogger('').addHandler(handler)


def setup_debug_logging_to_file(config):
    formatter = logging.Formatter(config['logging']['debug_format'])
    handler = logging.handlers.RotatingFileHandler(
        config['logging']['debug_file'], maxBytes=10485760, backupCount=3)
    handler.setFormatter(formatter)

    logging.getLogger('').addHandler(handler)


class VerbosityFilter(logging.Filter):
    def __init__(self, verbosity_level, loglevels):
        self.verbosity_level = verbosity_level
        self.loglevels = loglevels

    def filter(self, record):
        for name, required_log_level in self.loglevels.items():
            if record.name == name or record.name.startswith(name + '.'):
                return record.levelno >= required_log_level

        if record.name.startswith('mopidy'):
            required_log_level = LOG_LEVELS[self.verbosity_level]['mopidy']
        else:
            required_log_level = LOG_LEVELS[self.verbosity_level]['root']
        return record.levelno >= required_log_level


class ColorizingStreamHandler(logging.StreamHandler):
    """
    Stream handler which colorizes the log using ANSI escape sequences.

    Does nothing on Windows, which doesn't support ANSI escape sequences.

    This implementation is based upon https://gist.github.com/vsajip/758430,
    which is:

        Copyright (C) 2010-2012 Vinay Sajip. All rights reserved.
        Licensed under the new BSD license.
    """

    color_map = {
        'black': 0,
        'red': 1,
        'green': 2,
        'yellow': 3,
        'blue': 4,
        'magenta': 5,
        'cyan': 6,
        'white': 7,
    }

    # Map logging levels to (background, foreground, bold/intense)
    level_map = {
        logging.DEBUG: (None, 'blue', False),
        logging.INFO: (None, 'white', False),
        logging.WARNING: (None, 'yellow', False),
        logging.ERROR: (None, 'red', False),
        logging.CRITICAL: ('red', 'white', True),
    }
    csi = '\x1b['
    reset = '\x1b[0m'

    is_windows = platform.system() == 'Windows'

    @property
    def is_tty(self):
        isatty = getattr(self.stream, 'isatty', None)
        return isatty and isatty()

    def emit(self, record):
        try:
            message = self.format(record)
            self.stream.write(message)
            self.stream.write(getattr(self, 'terminator', '\n'))
            self.flush()
        except Exception:
            self.handleError(record)

    def format(self, record):
        message = logging.StreamHandler.format(self, record)
        if not self.is_tty or self.is_windows:
            return message
        return self.colorize(message, record)

    def colorize(self, message, record):
        if record.levelno in self.level_map:
            bg, fg, bold = self.level_map[record.levelno]
            params = []
            if bg in self.color_map:
                params.append(str(self.color_map[bg] + 40))
            if fg in self.color_map:
                params.append(str(self.color_map[fg] + 30))
            if bold:
                params.append('1')
            if params:
                message = ''.join((
                    self.csi, ';'.join(params), 'm', message, self.reset))
        return message
