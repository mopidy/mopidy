import logging
import signal
import threading

import gobject
gobject.threads_init()

from pykka import ActorDeadError
from pykka.registry import ActorRegistry

from mopidy import SettingsError

logger = logging.getLogger('mopidy.utils.process')

def exit_handler(signum, frame):
    """A :mod:`signal` handler which will exit the program on signal."""
    signals = dict((k, v) for v, k in signal.__dict__.iteritems()
        if v.startswith('SIG') and not v.startswith('SIG_'))
    logger.info(u'Got %s. Exiting...', signals[signum])
    stop_all_actors()

def stop_all_actors():
    num_actors = len(ActorRegistry.get_all())
    while num_actors:
        logger.debug(u'Stopping %d actor(s)...', num_actors)
        ActorRegistry.stop_all()
        num_actors = len(ActorRegistry.get_all())

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


class GObjectEventThread(BaseThread):
    """
    A GObject event loop which is shared by all Mopidy components that uses
    libraries that need a GObject event loop, like GStreamer and D-Bus.

    Should be started by Mopidy's core and used by
    :mod:`mopidy.output.gstreamer`, :mod:`mopidy.frontend.mpris`, etc.
    """

    def __init__(self):
        super(GObjectEventThread, self).__init__()
        self.name = u'GObjectEventThread'
        self.loop = None

    def run_inside_try(self):
        self.loop = gobject.MainLoop().run()

    def destroy(self):
        self.loop.quit()
        super(GObjectEventThread, self).destroy()
