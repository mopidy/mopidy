import logging
import logging.handlers

from mopidy import settings

def setup_logging(verbosity_level, dump):
    setup_console_logging(verbosity_level)
    if dump:
        setup_dump_logging()

def setup_console_logging(verbosity_level):
    if verbosity_level == 0:
        level = logging.WARNING
    elif verbosity_level == 2:
        level = logging.DEBUG
    else:
        level = logging.INFO
    logging.basicConfig(format=settings.CONSOLE_LOG_FORMAT, level=level)

def setup_dump_logging():
    root = logging.getLogger('')
    root.setLevel(logging.DEBUG)
    formatter = logging.Formatter(settings.DUMP_LOG_FORMAT)
    handler = logging.handlers.RotatingFileHandler(
        settings.DUMP_LOG_FILENAME, maxBytes=102400, backupCount=3)
    handler.setFormatter(formatter)
    root.addHandler(handler)

def indent(string, places=4, linebreak='\n'):
    lines = string.split(linebreak)
    if len(lines) == 1:
        return string
    result = u''
    for line in lines:
        result += linebreak + ' ' * places + line
    return result
