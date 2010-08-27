import logging
import multiprocessing
import multiprocessing.dummy
from multiprocessing.reduction import reduce_connection
import pickle
import sys

from mopidy import SettingsError

logger = logging.getLogger('mopidy.utils.process')

def pickle_connection(connection):
    return pickle.dumps(reduce_connection(connection))

def unpickle_connection(pickled_connection):
    # From http://stackoverflow.com/questions/1446004
    (func, args) = pickle.loads(pickled_connection)
    return func(*args)


class BaseProcess(multiprocessing.Process):
    def run(self):
        logger.debug(u'%s: Starting process', self.name)
        try:
            self.run_inside_try()
        except KeyboardInterrupt:
            logger.info(u'%s: Interrupted by user', self.name)
            sys.exit(0)
        except SettingsError as e:
            logger.error(e.message)
            sys.exit(1)
        except ImportError as e:
            logger.error(e)
            sys.exit(1)
        except Exception as e:
            logger.exception(e)
            raise e

    def run_inside_try(self):
        raise NotImplementedError

    def destroy(self):
        self.terminate()


class BaseThread(multiprocessing.dummy.Process):
    def run(self):
        logger.debug(u'%s: Starting process', self.name)
        try:
            self.run_inside_try()
        except KeyboardInterrupt:
            logger.info(u'%s: Interrupted by user', self.name)
            sys.exit(0)
        except SettingsError as e:
            logger.error(e.message)
            sys.exit(1)
        except ImportError as e:
            logger.error(e)
            sys.exit(1)
        except Exception as e:
            logger.exception(e)
            raise e

    def run_inside_try(self):
        raise NotImplementedError

    def destroy(self):
        pass
