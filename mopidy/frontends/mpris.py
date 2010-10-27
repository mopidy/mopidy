import logging
import multiprocessing
import socket
import time

try:
    import dbus
except ImportError as import_error:
    from mopidy import OptionalDependencyError
    raise OptionalDependencyError(import_error)

from mopidy import get_version, settings, SettingsError
from mopidy.frontends.base import BaseFrontend
from mopidy.utils.process import BaseThread

logger = logging.getLogger('mopidy.frontends.mpris')

BUS_NAME = u'org.mpris.MediaPlayer2.mopidy'

class MprisFrontend(BaseFrontend):
    """
    Frontend which lets you control Mopidy through the Media Player Remote
    Interfacing Specification (MPRIS) D-Bus interface.

    An example of an MPRIS client is Ubuntu's audio indicator applet.

    **Dependencies:**

    - ``dbus`` Python bindings. The package is named ``python-dbus`` in
      Ubuntu/Debian.
    """

    def __init__(self, *args, **kwargs):
        super(MprisFrontend, self).__init__(*args, **kwargs)
        (self.connection, other_end) = multiprocessing.Pipe()
        self.thread = MprisFrontendThread(self.core_queue, other_end)

    def start(self):
        self.thread.start()

    def destroy(self):
        self.thread.destroy()

    def process_message(self, message):
        self.connection.send(message)


class MprisFrontendThread(BaseThread):
    def __init__(self, core_queue, connection):
        super(MprisFrontendThread, self).__init__(core_queue)
        self.name = u'MprisFrontendThread'
        self.connection = connection
        self.bus = None

    def run_inside_try(self):
        self.setup()
        while True:
            self.connection.poll(None)
            message = self.connection.recv()
            self.process_message(message)

    def setup(self):
        self.bus = dbus.SystemBus()
        logger.info(u'Connected to D-Bus/MPRIS')

    def process_message(self, message):
        pass # Ignore commands for other frontends
