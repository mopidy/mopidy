from __future__ import unicode_literals

import contextlib
import logging
import time


logger = logging.getLogger(__name__)
TRACE = logging.getLevelName('TRACE')


@contextlib.contextmanager
def time_logger(name, level=TRACE):
    start = time.time()
    yield
    logger.log(level, '%s took %dms', name, (time.time() - start) * 1000)
