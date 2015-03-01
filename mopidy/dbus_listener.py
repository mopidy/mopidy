from __future__ import absolute_import, unicode_literals

import logging

from dbus.mainloop.glib import DBusGMainLoop  # integration into the main loop

from mopidy.core.listener import CoreListener

logger = logging.getLogger(__name__)

try:
    import dbus
except ImportError:
    dbus = None


class DbusListener(object):
    """Listen to events emitted via DBus."""

    def __init__(self):
        try:
            DBusGMainLoop(set_as_default=True)  # integrate into main loop
            bus = dbus.SystemBus()  # connect to system wide dbus
            # define the signal to listen to
            bus.add_signal_receiver(
                self.handle_suspend,               # callback function
                'PrepareForSleep',                 # signal name
                'org.freedesktop.login1.Manager',  # interface
                'org.freedesktop.login1'           # bus name
            )
            # define the signal to listen to
            bus.add_signal_receiver(
                self.handle_shutdown,              # callback function
                'PrepareForShutdown',              # signal name
                'org.freedesktop.login1.Manager',  # interface
                'org.freedesktop.login1'           # bus name
            )
            logger.info('Dbus signal receivers added successfully')
        except dbus.exceptions.DBusException as e:
            logger.debug('%s: Adding DBus listener failed: %s', self, e)
            return False

    def handle_suspend(self, suspend):
        logger.debug('DBus suspend signal received: %s', suspend)
        # Forward event from backend to frontends
        CoreListener.send('system_suspend', suspend=suspend)

    def handle_shutdown(self, shutdown):
        logger.debug('DBus shutdown signal received: %s', shutdown)
        # Forward event from backend to frontends
        CoreListener.send('system_shutdown', shutdown=shutdown)
