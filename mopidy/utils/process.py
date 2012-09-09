import logging
import signal
import sys
import thread
import threading
import traceback

from pykka import ActorDeadError
from pykka.registry import ActorRegistry

from mopidy import SettingsError

logger = logging.getLogger('mopidy.utils.process')

signals = dict((k, v) for v, k in signal.__dict__.iteritems()
    if v.startswith('SIG') and not v.startswith('SIG_'))

def exit_process():
    logger.debug(u'Interrupting main...')
    thread.interrupt_main()
    logger.debug(u'Interrupted main')

def exit_handler(signum, frame):
    """A :mod:`signal` handler which will exit the program on signal."""
    logger.info(u'Got %s signal', signals[signum])
    exit_process()

def stop_actors_by_class(klass):
    actors = ActorRegistry.get_by_class(klass)
    logger.debug(u'Stopping %d instance(s) of %s', len(actors), klass.__name__)
    for actor in actors:
        actor.stop()

def stop_remaining_actors():
    num_actors = len(ActorRegistry.get_all())
    while num_actors:
        logger.error(
            u'There are actor threads still running, this is probably a bug')
        logger.debug(u'Seeing %d actor and %d non-actor thread(s): %s',
            num_actors, threading.active_count() - num_actors,
            ', '.join([t.name for t in threading.enumerate()]))
        logger.debug(u'Stopping %d actor(s)...', num_actors)
        ActorRegistry.stop_all()
        num_actors = len(ActorRegistry.get_all())
    logger.debug(u'All actors stopped.')

class BaseThread(threading.Thread):
    def __init__(self):
        super(BaseThread, self).__init__()
        # No thread should block process from exiting
        self.daemon = True

    def run(self):
        logger.debug(u'%s: Starting thread', self.name)
        try:
            self.run_inside_try()
        except KeyboardInterrupt:
            logger.info(u'Interrupted by user')
        except SettingsError as e:
            logger.error(e.message)
        except ImportError as e:
            logger.error(e)
        except ActorDeadError as e:
            logger.warning(e)
        except Exception as e:
            logger.exception(e)
        logger.debug(u'%s: Exiting thread', self.name)

    def run_inside_try(self):
        raise NotImplementedError

class DebugThread(threading.Thread):
    daemon = True
    name = 'DebugThread'

    event = threading.Event()

    def handler(self, signum, frame):
        logger.info(u'Got %s signal', signals[signum])
        self.event.set()

    def run(self):
        while True:
            self.event.wait()
            threads = dict((t.ident, t.name) for t in threading.enumerate())

            for ident, frame in sys._current_frames().items():
                if self.ident == ident:
                    continue

                print "## Thread: %s (%s) ##" % (threads[ident], ident)
                print ''.join(traceback.format_stack(frame))

            self.event.clear()
