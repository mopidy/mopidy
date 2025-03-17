from __future__ import annotations

import logging
import logging.config
import logging.handlers
import platform
from logging import LogRecord
from typing import TYPE_CHECKING, ClassVar, Literal

if TYPE_CHECKING:
    from mopidy.config import Config, LoggingConfig

LogLevelName = Literal[
    "critical",
    "error",
    "warning",
    "info",
    "debug",
    "trace",
    "all",
]

LogColorName = Literal[
    "black",
    "red",
    "green",
    "yellow",
    "blue",
    "magenta",
    "cyan",
    "white",
]

LOG_LEVELS: dict[int, dict[str, int]] = {
    -1: {"root": logging.ERROR, "mopidy": logging.WARNING},
    0: {"root": logging.ERROR, "mopidy": logging.INFO},
    1: {"root": logging.WARNING, "mopidy": logging.DEBUG},
    2: {"root": logging.INFO, "mopidy": logging.DEBUG},
    3: {"root": logging.DEBUG, "mopidy": logging.DEBUG},
    4: {"root": logging.NOTSET, "mopidy": logging.NOTSET},
}

# Custom log level which has even lower priority than DEBUG
TRACE_LOG_LEVEL = 5
logging.addLevelName(TRACE_LOG_LEVEL, "TRACE")

logger = logging.getLogger(__name__)


class DelayedHandler(logging.Handler):
    def __init__(self) -> None:
        logging.Handler.__init__(self)
        self._released = False
        self._buffer: list[LogRecord] = []

    def handle(self, record: LogRecord) -> bool:
        if not self._released:
            self._buffer.append(record)
        return True

    def release_delayed_logs(self) -> None:
        self._released = True
        root = logging.getLogger("")
        while self._buffer:
            root.handle(self._buffer.pop(0))


_delayed_handler = DelayedHandler()


def bootstrap_delayed_logging() -> None:
    root = logging.getLogger("")
    root.setLevel(logging.NOTSET)
    root.addHandler(_delayed_handler)


def setup_logging(
    config: Config,
    base_verbosity_level: int,
    args_verbosity_level: int,
) -> None:
    logging.captureWarnings(True)

    if config["logging"]["config_file"]:
        # Logging config from file must be read before other handlers are
        # added. If not, the other handlers will have no effect.
        path = config["logging"]["config_file"]
        try:
            logging.config.fileConfig(path, disable_existing_loggers=False)
        except Exception as exc:  # noqa: BLE001
            # Catch everything as logging does not specify what can go wrong.
            logger.error("Loading logging config %r failed. %s", path, exc)

    loglevels = config.get("loglevels", {})

    verbosity_level = get_verbosity_level(
        config["logging"],
        base_verbosity_level,
        args_verbosity_level,
    )
    verbosity_filter = VerbosityFilter(verbosity_level, loglevels)

    formatter = logging.Formatter(config["logging"]["format"])

    handler: logging.StreamHandler
    if config["logging"]["color"]:
        handler = ColorizingStreamHandler(config.get("logcolors", {}))
    else:
        handler = logging.StreamHandler()
    handler.addFilter(verbosity_filter)
    handler.setFormatter(formatter)

    logging.getLogger("").addHandler(handler)

    _delayed_handler.release_delayed_logs()


def get_verbosity_level(
    logging_config: LoggingConfig,
    base_verbosity_level: int,
    args_verbosity_level: int,
) -> int:
    if args_verbosity_level:
        result = base_verbosity_level + args_verbosity_level
    else:
        result = base_verbosity_level + (logging_config["verbosity"] or 0)

    result = max(result, min(LOG_LEVELS.keys()))
    result = min(result, max(LOG_LEVELS.keys()))

    return result


class VerbosityFilter(logging.Filter):
    def __init__(self, verbosity_level: int, loglevels: dict[LogLevelName, int]):
        super().__init__()
        self.verbosity_level = verbosity_level
        self.loglevels = loglevels

    def filter(self, record: LogRecord) -> bool:
        for name, required_log_level in self.loglevels.items():
            if record.name == name or record.name.startswith(name + "."):
                return record.levelno >= required_log_level

        if record.name.startswith("mopidy"):
            required_log_level = LOG_LEVELS[self.verbosity_level]["mopidy"]
        else:
            required_log_level = LOG_LEVELS[self.verbosity_level]["root"]
        return record.levelno >= required_log_level


#: Available log colors.
COLORS: list[LogColorName] = [
    "black",
    "red",
    "green",
    "yellow",
    "blue",
    "magenta",
    "cyan",
    "white",
]


class ColorizingStreamHandler(logging.StreamHandler):
    """
    Stream handler which colorizes the log using ANSI escape sequences.

    Does nothing on Windows, which doesn't support ANSI escape sequences.

    This implementation is based upon https://gist.github.com/vsajip/758430,
    which is:

        Copyright (C) 2010-2012 Vinay Sajip. All rights reserved.
        Licensed under the new BSD license.
    """

    # Map logging levels to (background, foreground, bold/intense)
    level_map: ClassVar[dict[int, tuple[LogColorName | None, LogColorName, bool]]] = {
        TRACE_LOG_LEVEL: (None, "blue", False),
        logging.DEBUG: (None, "blue", False),
        logging.INFO: (None, "white", False),
        logging.WARNING: (None, "yellow", False),
        logging.ERROR: (None, "red", False),
        logging.CRITICAL: ("red", "white", True),
    }
    # Map logger name to foreground colors
    logger_map: dict[LogLevelName, LogColorName]

    csi = "\x1b["
    reset = "\x1b[0m"

    is_windows = platform.system() == "Windows"

    def __init__(self, logger_colors: dict[LogLevelName, LogColorName]) -> None:
        super().__init__()
        self.logger_map = logger_colors

    @property
    def is_tty(self) -> bool:
        isatty = getattr(self.stream, "isatty", None)
        return isatty is not None and isatty()

    def emit(self, record: LogRecord) -> None:
        try:
            message = self.format(record)
            self.stream.write(message)
            self.stream.write(getattr(self, "terminator", "\n"))
            self.flush()
        except Exception:  # noqa: BLE001
            self.handleError(record)

    def format(self, record: LogRecord) -> str:
        message = logging.StreamHandler.format(self, record)
        if not self.is_tty or self.is_windows:
            return message
        for name, color in self.logger_map.items():
            if record.name.startswith(name):
                return self.colorize(message, fg=color)
        if record.levelno in self.level_map:
            bg, fg, bold = self.level_map[record.levelno]
            return self.colorize(message, bg=bg, fg=fg, bold=bold)
        return message

    def colorize(
        self,
        message: str,
        bg: LogColorName | None = None,
        fg: LogColorName | None = None,
        bold: bool = False,
    ) -> str:
        params = []
        if bg in COLORS:
            params.append(str(COLORS.index(bg) + 40))
        if fg in COLORS:
            params.append(str(COLORS.index(fg) + 30))
        if bold:
            params.append("1")
        if params:
            message = "".join((self.csi, ";".join(params), "m", message, self.reset))
        return message
