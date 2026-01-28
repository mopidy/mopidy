from __future__ import annotations

import logging
import logging.config
import logging.handlers
from contextvars import ContextVar
from typing import TYPE_CHECKING, override

if TYPE_CHECKING:
    from mopidy.config import Config
    from mopidy.config.types import LogLevelName

logger = logging.getLogger(__name__)


LOG_LEVELS: dict[int, dict[str, int]] = {
    -1: {"root": logging.ERROR, "mopidy": logging.ERROR},
    0: {"root": logging.ERROR, "mopidy": logging.WARNING},
    1: {"root": logging.WARNING, "mopidy": logging.INFO},
    2: {"root": logging.INFO, "mopidy": logging.DEBUG},
    3: {"root": logging.DEBUG, "mopidy": logging.DEBUG},
    4: {"root": logging.NOTSET, "mopidy": logging.NOTSET},
}


class DelayedHandler(logging.handlers.MemoryHandler):
    def __init__(self) -> None:
        super().__init__(
            # Flush all records immediately.
            flushLevel=logging.NOTSET,
            # Ensure we have enough space for all logging from early startup,
            # until we set the target handler to flush to.
            capacity=1000,
        )

    @override
    def shouldFlush(self, record: logging.LogRecord) -> bool:
        return self.target is not None


_delayed_handler_ctx = ContextVar[DelayedHandler | None](
    "delayed_handler",
    default=None,
)


def bootstrap_delayed_logging() -> None:
    root = logging.getLogger("")
    root.setLevel(logging.NOTSET)
    root.addHandler(delayed_handler := DelayedHandler())
    _delayed_handler_ctx.set(delayed_handler)


def setup_logging(
    *,
    config: Config,
    verbosity_level: int,
) -> None:
    logging.captureWarnings(True)

    if path := config["logging"]["config_file"]:
        # Logging config from file must be read before other handlers are
        # added. If not, the other handlers will have no effect.
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

    handler = logging.StreamHandler()
    handler.addFilter(verbosity_filter)
    handler.setFormatter(formatter)

    if delayed_handler := _delayed_handler_ctx.get():
        delayed_handler.setTarget(handler)


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
