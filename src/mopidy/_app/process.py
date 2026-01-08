from __future__ import annotations

import logging
import signal
import threading
from types import FrameType
from typing import TYPE_CHECKING

import pykka.debug

from mopidy._lib import paths, process

if TYPE_CHECKING:
    from mopidy.config import Config

logger = logging.getLogger(__name__)


def setup_signal_handlers() -> None:
    signal.signal(signal.SIGTERM, sigterm_handler)
    # Windows does not have signal.SIGUSR1
    if hasattr(signal, "SIGUSR1"):
        signal.signal(signal.SIGUSR1, pykka.debug.log_thread_tracebacks)


def create_app_dirs(config: Config) -> None:
    paths.get_or_create_dir(config["core"]["cache_dir"])
    paths.get_or_create_dir(config["core"]["config_dir"])
    paths.get_or_create_dir(config["core"]["data_dir"])


def sigterm_handler(_signum: int, _frame: FrameType | None) -> None:
    """A :mod:`signal` handler which will exit the program on signal.

    This function is not called when the process' main thread is running a GLib
    mainloop. In that case, the GLib mainloop must listen for SIGTERM signals
    and quit itself.

    For Mopidy subcommands that does not run the GLib mainloop, this handler
    ensures a proper shutdown of the process on SIGTERM.
    """
    logger.info("Got SIGTERM signal. Exiting...")
    process.exit_process()


def stop_actors_by_class(klass: type[pykka.Actor]) -> None:
    actors = pykka.ActorRegistry.get_by_class(klass)
    logger.debug("Stopping %d instance(s) of %s", len(actors), klass.__name__)
    for actor in actors:
        actor.stop()


def stop_remaining_actors() -> None:
    num_actors = len(pykka.ActorRegistry.get_all())
    while num_actors:
        logger.error("There are actor threads still running, this is probably a bug")
        logger.debug(
            "Seeing %d actor and %d non-actor thread(s): %s",
            num_actors,
            threading.active_count() - num_actors,
            ", ".join(t.name for t in threading.enumerate()),
        )
        logger.debug("Stopping %d actor(s)...", num_actors)
        pykka.ActorRegistry.stop_all()
        num_actors = len(pykka.ActorRegistry.get_all())
    logger.debug("All actors stopped.")
