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
    def __init__(self, core_queue):
        super(BaseProcess, self).__init__()
        self.core_queue = core_queue

    def run(self):
        logger.debug(u'%s: Starting process', self.name)
        try:
            self.run_inside_try()
        except KeyboardInterrupt:
            logger.info(u'Interrupted by user')
            self.exit(0, u'Interrupted by user')
        except SettingsError as e:
            logger.error(e.message)
            self.exit(1, u'Settings error')
        except ImportError as e:
            logger.error(e)
            self.exit(2, u'Import error')
        except Exception as e:
            logger.exception(e)
            self.exit(3, u'Unknown error')

    def run_inside_try(self):
        raise NotImplementedError

    def destroy(self):
        self.terminate()

    def exit(self, status=0, reason=None):
        self.core_queue.put({'to': 'core', 'command': 'exit',
            'status': status, 'reason': reason})
        self.destroy()


class BaseThread(multiprocessing.dummy.Process):
    def __init__(self, core_queue):
        super(BaseThread, self).__init__()
        self.core_queue = core_queue

    def run(self):
        logger.debug(u'%s: Starting thread', self.name)
        try:
            self.run_inside_try()
        except KeyboardInterrupt:
            logger.info(u'Interrupted by user')
            self.exit(0, u'Interrupted by user')
        except SettingsError as e:
            logger.error(e.message)
            self.exit(1, u'Settings error')
        except ImportError as e:
            logger.error(e)
            self.exit(2, u'Import error')
        except Exception as e:
            logger.exception(e)
            self.exit(3, u'Unknown error')

    def run_inside_try(self):
        raise NotImplementedError

    def destroy(self):
        pass

    def exit(self, status=0, reason=None):
        self.core_queue.put({'to': 'core', 'command': 'exit',
            'status': status, 'reason': reason})
        self.destroy()
