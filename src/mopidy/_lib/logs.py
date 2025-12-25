import contextlib
import logging
import time
from collections.abc import Generator

logger = logging.getLogger(__name__)


# Custom log level which has even lower priority than DEBUG
TRACE_LOG_LEVEL = 5
logging.addLevelName(TRACE_LOG_LEVEL, "TRACE")


@contextlib.contextmanager
def log_time_spent(name: str, level: int = TRACE_LOG_LEVEL) -> Generator[None]:
    start = time.time()
    yield
    logger.log(level, "%s took %dms", name, (time.time() - start) * 1000)
