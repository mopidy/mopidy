import logging
import threading

import gobject
gobject.threads_init()

from mopidy import SettingsError

logger = logging.getLogger('mopidy.utils.process')


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
        self.destroy()


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
