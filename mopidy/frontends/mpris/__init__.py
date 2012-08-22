import logging

logger = logging.getLogger('mopidy.frontends.mpris')

try:
    import indicate
except ImportError as import_error:
    indicate = None
    logger.debug(u'Startup notification will not be sent (%s)', import_error)

from pykka.actor import ThreadingActor

from mopidy import settings
from mopidy.frontends.mpris import objects
from mopidy.listeners import BackendListener


class MprisFrontend(ThreadingActor, BackendListener):
    """
    Frontend which lets you control Mopidy through the Media Player Remote
    Interfacing Specification (`MPRIS <http://www.mpris.org/>`_) D-Bus
    interface.

    An example of an MPRIS client is the `Ubuntu Sound Menu
    <https://wiki.ubuntu.com/SoundMenu>`_.

    **Dependencies:**

    - D-Bus Python bindings. The package is named ``python-dbus`` in
      Ubuntu/Debian.
    - ``libindicate`` Python bindings is needed to expose Mopidy in e.g. the
      Ubuntu Sound Menu. The package is named ``python-indicate`` in
      Ubuntu/Debian.
    - An ``.desktop`` file for Mopidy installed at the path set in
      :attr:`mopidy.settings.DESKTOP_FILE`. See :ref:`install_desktop_file` for
      details.

    **Testing the frontend**

    To test, start Mopidy, and then run the following in a Python shell::

        import dbus
        bus = dbus.SessionBus()
        player = bus.get_object('org.mpris.MediaPlayer2.mopidy',
            '/org/mpris/MediaPlayer2')

    Now you can control Mopidy through the player object. Examples:

    - To get some properties from Mopidy, run::

        props = player.GetAll('org.mpris.MediaPlayer2',
            dbus_interface='org.freedesktop.DBus.Properties')

    - To quit Mopidy through D-Bus, run::

        player.Quit(dbus_interface='org.mpris.MediaPlayer2')
    """

    def __init__(self):
        super(MprisFrontend, self).__init__()
        self.indicate_server = None
        self.mpris_object = None

    def on_start(self):
        try:
            self.mpris_object = objects.MprisObject()
            self._send_startup_notification()
        except Exception as e:
            logger.error(u'MPRIS frontend setup failed (%s)', e)
            self.stop()

    def on_stop(self):
        logger.debug(u'Removing MPRIS object from D-Bus connection...')
        if self.mpris_object:
            self.mpris_object.remove_from_connection()
            self.mpris_object = None
        logger.debug(u'Removed MPRIS object from D-Bus connection')

    def _send_startup_notification(self):
        """
        Send startup notification using libindicate to make Mopidy appear in
        e.g. `Ubuntu's sound menu <https://wiki.ubuntu.com/SoundMenu>`_.

        A reference to the libindicate server is kept for as long as Mopidy is
        running. When Mopidy exits, the server will be unreferenced and Mopidy
        will automatically be unregistered from e.g. the sound menu.
        """
        if not indicate:
            return
        logger.debug(u'Sending startup notification...')
        self.indicate_server = indicate.Server()
        self.indicate_server.set_type('music.mopidy')
        self.indicate_server.set_desktop_file(settings.DESKTOP_FILE)
        self.indicate_server.show()
        logger.debug(u'Startup notification sent')

    def _emit_properties_changed(self, *changed_properties):
        if self.mpris_object is None:
            return
        props_with_new_values = [
            (p, self.mpris_object.Get(objects.PLAYER_IFACE, p))
            for p in changed_properties]
        self.mpris_object.PropertiesChanged(objects.PLAYER_IFACE,
            dict(props_with_new_values), [])

    def track_playback_paused(self, track, time_position):
        logger.debug(u'Received track playback paused event')
        self._emit_properties_changed('PlaybackStatus')

    def track_playback_resumed(self, track, time_position):
        logger.debug(u'Received track playback resumed event')
        self._emit_properties_changed('PlaybackStatus')

    def track_playback_started(self, track):
        logger.debug(u'Received track playback started event')
        self._emit_properties_changed('PlaybackStatus', 'Metadata')

    def track_playback_ended(self, track, time_position):
        logger.debug(u'Received track playback ended event')
        self._emit_properties_changed('PlaybackStatus', 'Metadata')

    def volume_changed(self):
        logger.debug(u'Received volume changed event')
        self._emit_properties_changed('Volume')

    def seeked(self):
        logger.debug(u'Received seeked event')
        if self.mpris_object is None:
            return
        self.mpris_object.Seeked(
            self.mpris_object.Get(objects.PLAYER_IFACE, 'Position'))
