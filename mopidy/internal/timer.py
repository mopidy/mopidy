from __future__ import unicode_literals

import contextlib
import logging
import time

from mopidy.internal import log


logger = logging.getLogger(__name__)


@contextlib.contextmanager
def time_logger(name, level=log.TRACE_LOG_LEVEL):
    start = time.time()
    yield
    logger.log(level, '%s took %dms', name, (time.time() - start) * 1000)
