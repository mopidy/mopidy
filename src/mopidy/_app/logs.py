from __future__ import annotations

import logging
import logging.config
import platform
from typing import TYPE_CHECKING, ClassVar, get_args

from mopidy._lib.logs import TRACE_LOG_LEVEL
from mopidy.config.types import LogColorName

if TYPE_CHECKING:
    from mopidy.config import Config
    from mopidy.config.types import LogLevelName

logger = logging.getLogger(__name__)


LOG_LEVELS: dict[int, dict[str, int]] = {
    -1: {"root": logging.ERROR, "mopidy": logging.WARNING},
    0: {"root": logging.ERROR, "mopidy": logging.INFO},
    1: {"root": logging.WARNING, "mopidy": logging.DEBUG},
    2: {"root": logging.INFO, "mopidy": logging.DEBUG},
    3: {"root": logging.DEBUG, "mopidy": logging.DEBUG},
    4: {"root": logging.NOTSET, "mopidy": logging.NOTSET},
}


class DelayedHandler(logging.Handler):
    def __init__(self) -> None:
        logging.Handler.__init__(self)
        self._released = False
        self._buffer: list[logging.LogRecord] = []

    def handle(self, record: logging.LogRecord) -> bool:
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
    *,
    config: Config,
    verbosity_level: int,
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

    verbosity_filter = VerbosityFilter(
        verbosity_level=get_verbosity_level(
            config_value=config["logging"]["verbosity"],
            cli_value=verbosity_level,
        ),
        loglevels=config.get("loglevels", {}),
    )

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
    *,
    config_value: int | None,
    cli_value: int,
) -> int:
    result = cli_value or config_value or 0
    result = max(result, min(LOG_LEVELS.keys()))
    result = min(result, max(LOG_LEVELS.keys()))
    return result


class VerbosityFilter(logging.Filter):
    def __init__(
        self,
        *,
        verbosity_level: int,
        loglevels: dict[LogLevelName, int],
    ) -> None:
        super().__init__()
        self.verbosity_level = verbosity_level
        self.loglevels = loglevels

    def filter(self, record: logging.LogRecord) -> bool:
        for name, required_log_level in self.loglevels.items():
            if record.name == name or record.name.startswith(name + "."):
                return record.levelno >= required_log_level

        if record.name.startswith("mopidy"):
            required_log_level = LOG_LEVELS[self.verbosity_level]["mopidy"]
        else:
            required_log_level = LOG_LEVELS[self.verbosity_level]["root"]
        return record.levelno >= required_log_level


class ColorizingStreamHandler(logging.StreamHandler):
    """Stream handler which colorizes the log using ANSI escape sequences.

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

    # Color names
    color_names = get_args(LogColorName)

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

    def emit(self, record: logging.LogRecord) -> None:
        try:
            message = self.format(record)
            self.stream.write(message)
            self.stream.write(getattr(self, "terminator", "\n"))
            self.flush()
        except Exception:  # noqa: BLE001
            self.handleError(record)

    def format(self, record: logging.LogRecord) -> str:
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
        if bg in self.color_names:
            params.append(str(self.color_names.index(bg) + 40))
        if fg in self.color_names:
            params.append(str(self.color_names.index(fg) + 30))
        if bold:
            params.append("1")
        if params:
            message = "".join((self.csi, ";".join(params), "m", message, self.reset))
        return message
