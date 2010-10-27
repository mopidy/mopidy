import gobject
gobject.threads_init()

import logging
import multiprocessing

try:
    import dbus
    import dbus.service
    from dbus.mainloop.glib import DBusGMainLoop
except ImportError as import_error:
    from mopidy import OptionalDependencyError
    raise OptionalDependencyError(import_error)

from mopidy.frontends.base import BaseFrontend
from mopidy.utils.process import BaseThread

logger = logging.getLogger('mopidy.frontends.mpris')


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
        self.dbus_objects = []

    def destroy(self):
        for dbus_object in self.dbus_objects:
            dbus_object.remove_from_connection()
        self.dbus_objects = []

    def run_inside_try(self):
        self.setup()
        while True:
            self.connection.poll(None)
            message = self.connection.recv()
            self.process_message(message)

    def setup(self):
        self.dbus_objects.append(MprisObject(self.core_queue))

        # TODO Move to another thread if we need to process messages
        logger.debug(u'Starting GLib main loop')
        loop = gobject.MainLoop()
        loop.run()

    def process_message(self, message):
        pass # Ignore commands for other frontends


class MprisObject(dbus.service.Object):
    """Implements http://www.mpris.org/2.0/spec/"""

    bus_name = 'org.mpris.MediaPlayer2.mopidy'
    object_path = '/org/mpris/MediaPlayer2'
    property_interface = 'org.freedesktop.DBus.Properties'
    root_interface = 'org.mpris.MediaPlayer2'
    player_interface = 'org.mpris.MediaPlayer2.Player'
    properties = {
        root_interface: {
            'CanQuit': (True, None),
            'CanRaise': (False, None),
            # TODO Add track list support
            'HasTrackList': (False, None),
            'Identity': ('Mopidy', None),
            # TODO Return URI schemes supported by backend configuration
            'SupportedUriSchemes': (dbus.Array(signature='s'), None),
            # TODO Return MIME types supported by local backend if active
            'SupportedMimeTypes': (dbus.Array(signature='s'), None),
        },
        player_interface: {
            # TODO
        },
    }

    def __init__(self, core_queue):
        self.core_queue = core_queue
        logger.debug(u'Prepare the D-Bus main loop before connecting')
        DBusGMainLoop(set_as_default=True)
        logger.info(u'Connecting to D-Bus')
        bus = dbus.SessionBus()
        logger.debug(u'Connecting to D-Bus: claiming service name')
        # FIXME We segfault at the next line 80% of the time
        bus_name = dbus.service.BusName(self.bus_name, bus)
        logger.debug(u'Connecting to D-Bus: registering service object')
        super(MprisObject, self).__init__(object_path=self.object_path,
            bus_name=bus_name)
        logger.debug(u'Connecting to D-Bus: done')


    ### Property interface

    @dbus.service.method(dbus_interface=property_interface,
        in_signature='ss', out_signature='v')
    def Get(self, interface, prop):
        getter, setter = self.properties[interface][prop]
        return getter() if callable(getter) else getter

    @dbus.service.method(dbus_interface=property_interface,
        in_signature='s', out_signature='a{sv}')
    def GetAll(self, interface):
        """
        To test, start Mopidy and then run the following in a Python shell::

            import dbus
            bus = dbus.SessionBus()
            player = bus.get_object('org.mpris.MediaPlayer2.mopidy',
                '/org/mpris/MediaPlayer2')
            props = player.GetAll('org.mpris.MediaPlayer2',
                dbus_interface='org.freedesktop.DBus.Properties')
        """
        getters = {}
        for key, (getter, setter) in self.properties[interface].iteritems():
            getters[key] = getter() if callable(getter) else getter
        return getters

    @dbus.service.method(dbus_interface=property_interface,
        in_signature='ssv', out_signature='')
    def Set(self, interface, prop, value):
        getter, setter = self.properties[interface][prop]
        if setter is not None:
            setter(value)


    ### Root interface

    @dbus.service.method(dbus_interface=root_interface)
    def Raise(self):
        pass # We do not have a GUI

    @dbus.service.method(dbus_interface=root_interface)
    def Quit(self):
        """
        To test, start Mopidy and then run the following in a Python shell::

            import dbus
            bus = dbus.SessionBus()
            player = bus.get_object('org.mpris.MediaPlayer2.mopidy',
                '/org/mpris/MediaPlayer2')
            player.Quit(dbus_interface='org.mpris.MediaPlayer2')
        """
        self.core_queue.put({'to': 'core', 'command': 'exit'})


    ### Player interface

    # TODO
