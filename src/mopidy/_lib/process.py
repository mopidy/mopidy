from __future__ import annotations

import _thread
import logging

logger = logging.getLogger(__name__)


def exit_process() -> None:
    logger.debug("Interrupting main...")
    _thread.interrupt_main()
    logger.debug("Interrupted main")
