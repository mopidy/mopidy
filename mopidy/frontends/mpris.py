import logging

try:
    import dbus
    import dbus.mainloop.glib
    import dbus.service
    import gobject
except ImportError as import_error:
    from mopidy import OptionalDependencyError
    raise OptionalDependencyError(import_error)

from pykka.actor import ThreadingActor
from pykka.registry import ActorRegistry

from mopidy.backends.base import Backend
from mopidy.backends.base.playback import PlaybackController
from mopidy.frontends.base import BaseFrontend
from mopidy.mixers.base import BaseMixer

logger = logging.getLogger('mopidy.frontends.mpris')

# Must be done before dbus.SessionBus() is called
gobject.threads_init()
dbus.mainloop.glib.threads_init()
dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)

BUS_NAME = 'org.mpris.MediaPlayer2.mopidy'
OBJECT_PATH = '/org/mpris/MediaPlayer2'
ROOT_IFACE = 'org.mpris.MediaPlayer2'
PLAYER_IFACE = 'org.mpris.MediaPlayer2.Player'


class MprisFrontend(ThreadingActor, BaseFrontend):
    """
    Frontend which lets you control Mopidy through the Media Player Remote
    Interfacing Specification (MPRIS) D-Bus interface.

    An example of an MPRIS client is `Ubuntu's sound menu
    <https://wiki.ubuntu.com/SoundMenu>`_.

    **Dependencies:**

    - ``dbus`` Python bindings. The package is named ``python-dbus`` in
      Ubuntu/Debian.
    - ``libindicate`` Python bindings is needed to expose Mopidy in e.g. the
      Ubuntu Sound Menu. The package is named ``python-indicate`` in
      Ubuntu/Debian.
    """

    # This thread requires :class:`mopidy.utils.process.GObjectEventThread` to be
    # running too. This is not enforced in any way by the code.

    def __init__(self):
        self.indicate_server = None
        self.dbus_objects = []

    def on_start(self):
        self.dbus_objects.append(MprisObject())
        self.send_startup_notification()

    def on_stop(self):
        for dbus_object in self.dbus_objects:
            dbus_object.remove_from_connection()
        self.dbus_objects = []

    def send_startup_notification(self):
        """
        Send startup notification using libindicate to make Mopidy appear in
        e.g. `Ubuntu's sound menu <https://wiki.ubuntu.com/SoundMenu>`_.

        A reference to the libindicate server is kept for as long as Mopidy is
        running. When Mopidy exits, the server will be unreferenced and Mopidy
        will automatically be unregistered from e.g. the sound menu.
        """
        try:
            import indicate
            self.indicate_server = indicate.Server()
            self.indicate_server.set_type('music.mopidy')
            # FIXME Location of .desktop file shouldn't be hardcoded
            self.indicate_server.set_desktop_file(
                '/usr/share/applications/mopidy.desktop')
            self.indicate_server.show()
        except ImportError as e:
            logger.debug(u'Startup notification was not sent. (%s)', e)


class MprisObject(dbus.service.Object):
    """Implements http://www.mpris.org/2.0/spec/"""

    properties = None

    def __init__(self):
        self._backend = None
        self._mixer = None
        self.properties = {
            ROOT_IFACE: self._get_root_iface_properties(),
            PLAYER_IFACE: self._get_player_iface_properties(),
        }
        bus_name = self._connect_to_dbus()
        super(MprisObject, self).__init__(bus_name, OBJECT_PATH)

    def _get_root_iface_properties(self):
        return {
            'CanQuit': (True, None),
            'CanRaise': (False, None),
            # TODO Add track list support
            'HasTrackList': (False, None),
            'Identity': ('Mopidy', None),
            'DesktopEntry': ('mopidy', None),
            # TODO Return URI schemes supported by backend configuration
            'SupportedUriSchemes': (dbus.Array([], signature='s'), None),
            # TODO Return MIME types supported by local backend if active
            'SupportedMimeTypes': (dbus.Array([], signature='s'), None),
        }

    def _get_player_iface_properties(self):
        return {
            'PlaybackStatus': (self.get_PlaybackStatus, None),
            'LoopStatus': (self.get_LoopStatus, self.set_LoopStatus),
            'Rate': (1.0, self.set_Rate),
            'Shuffle': (self.get_Shuffle, self.set_Shuffle),
            # TODO Get meta data
            'Metadata': ({
                'mpris:trackid': '', # TODO Use (cpid, track.uri)
            }, None),
            'Volume': (self.get_Volume, self.set_Volume),
            # TODO Get backend.playback.time_position
            'Position': (0, None),
            'MinimumRate': (1.0, None),
            'MaximumRate': (1.0, None),
            # TODO True if CanControl and backend.playback.track_at_next
            'CanGoNext': (False, None),
            # TODO True if CanControl and backend.playback.track_at_previous
            'CanGoPrevious': (False, None),
            # TODO True if CanControl and backend.playback.current_track
            'CanPlay': (False, None),
            # TODO True if CanControl and backend.playback.current_track
            'CanPause': (False, None),
            # TODO Set to True when the rest is implemented
            'CanSeek': (False, None),
            # TODO Set to True when the rest is implemented
            'CanControl': (False, None),
        }

    def _connect_to_dbus(self):
        logger.debug(u'Connecting to D-Bus...')
        bus_name = dbus.service.BusName(BUS_NAME, dbus.SessionBus())
        logger.info(u'Connected to D-Bus')
        return bus_name

    @property
    def backend(self):
        if self._backend is None:
            backend_refs = ActorRegistry.get_by_class(Backend)
            assert len(backend_refs) == 1, 'Expected exactly one running backend.'
            self._backend = backend_refs[0].proxy()
        return self._backend

    @property
    def mixer(self):
        if self._mixer is None:
            mixer_refs = ActorRegistry.get_by_class(BaseMixer)
            assert len(mixer_refs) == 1, 'Expected exactly one running mixer.'
            self._mixer = mixer_refs[0].proxy()
        return self._mixer


    ### Properties interface

    @dbus.service.method(dbus_interface=dbus.PROPERTIES_IFACE,
        in_signature='ss', out_signature='v')
    def Get(self, interface, prop):
        logger.debug(u'%s.Get(%s, %s) called',
            dbus.PROPERTIES_IFACE, repr(interface), repr(prop))
        (getter, setter) = self.properties[interface][prop]
        return getter() if callable(getter) else getter

    @dbus.service.method(dbus_interface=dbus.PROPERTIES_IFACE,
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
        logger.debug(u'%s.GetAll(%s) called',
            dbus.PROPERTIES_IFACE, repr(interface))
        getters = {}
        for key, (getter, setter) in self.properties[interface].iteritems():
            getters[key] = getter() if callable(getter) else getter
        return getters

    @dbus.service.method(dbus_interface=dbus.PROPERTIES_IFACE,
        in_signature='ssv', out_signature='')
    def Set(self, interface, prop, value):
        logger.debug(u'%s.Set(%s, %s, %s) called',
            dbus.PROPERTIES_IFACE, repr(interface), repr(prop), repr(value))
        getter, setter = self.properties[interface][prop]
        if setter is not None:
            setter(value)
            self.PropertiesChanged(interface,
                {prop: self.Get(interface, prop)}, [])

    @dbus.service.signal(dbus_interface=dbus.PROPERTIES_IFACE,
            signature='sa{sv}as')
    def PropertiesChanged(self, interface, changed_properties,
        invalidated_properties):
        logger.debug(u'%s.PropertiesChanged signaled', dbus.PROPERTIES_IFACE)
        pass


    ### Root interface methods

    @dbus.service.method(dbus_interface=ROOT_IFACE)
    def Raise(self):
        logger.debug(u'%s.Raise called', ROOT_IFACE)
        pass # We do not have a GUI

    @dbus.service.method(dbus_interface=ROOT_IFACE)
    def Quit(self):
        """
        To test, start Mopidy and then run the following in a Python shell::

            import dbus
            bus = dbus.SessionBus()
            player = bus.get_object('org.mpris.MediaPlayer2.mopidy',
                '/org/mpris/MediaPlayer2')
            player.Quit(dbus_interface='org.mpris.MediaPlayer2')
        """
        logger.debug(u'%s.Quit called', ROOT_IFACE)
        ActorRegistry.stop_all()


    ### Player interface methods

    @dbus.service.method(dbus_interface=PLAYER_IFACE)
    def Next(self):
        logger.debug(u'%s.Next called', PLAYER_IFACE)
        self.backend.playback.next().get()

    @dbus.service.method(dbus_interface=PLAYER_IFACE)
    def Previous(self):
        logger.debug(u'%s.Previous called', PLAYER_IFACE)
        self.backend.playback.previous().get()

    @dbus.service.method(dbus_interface=PLAYER_IFACE)
    def Pause(self):
        logger.debug(u'%s.Pause called', PLAYER_IFACE)
        self.backend.playback.pause().get()

    @dbus.service.method(dbus_interface=PLAYER_IFACE)
    def PlayPause(self):
        logger.debug(u'%s.PlayPause called', PLAYER_IFACE)
        state = self.backend.playback.state.get()
        if state == PlaybackController.PLAYING:
            self.backend.playback.pause().get()
        elif state == PlaybackController.PAUSED:
            self.backend.playback.resume().get()
        elif state == PlaybackController.STOPPED:
            self.backend.playback.play().get()

    @dbus.service.method(dbus_interface=PLAYER_IFACE)
    def Stop(self):
        logger.debug(u'%s.Stop called', PLAYER_IFACE)
        self.backend.playback.stop().get()

    @dbus.service.method(dbus_interface=PLAYER_IFACE)
    def Play(self):
        logger.debug(u'%s.Play called', PLAYER_IFACE)
        state = self.backend.playback.state.get()
        if state == PlaybackController.PAUSED:
            self.backend.playback.resume().get()
        else:
            self.backend.playback.play().get()

    @dbus.service.method(dbus_interface=PLAYER_IFACE)
    def Seek(self, offset):
        logger.debug(u'%s.Seek called', PLAYER_IFACE)
        offset_in_milliseconds = offset // 1000
        current_position = self.backend.playback.time_position.get()
        new_position = current_position + offset_in_milliseconds
        self.backend.playback.seek(new_position)

    @dbus.service.method(dbus_interface=PLAYER_IFACE)
    def SetPosition(self, track_id, position):
        logger.debug(u'%s.SetPosition called', PLAYER_IFACE)
        position = position // 1000
        current_track = self.backend.playback.current_track.get()
        # TODO Currently the ID is assumed to be the URI of the track. This
        # should be changed to a D-Bus object ID than can be mapped to the CPID
        # and URI of the track.
        if current_track and current_track.uri != track_id:
            return
        if position < 0:
            return
        if current_track and current_track.length < position:
            return
        self.backend.playback.seek(position)

    @dbus.service.method(dbus_interface=PLAYER_IFACE)
    def OpenUri(self, uri):
        logger.debug(u'%s.OpenUri called', PLAYER_IFACE)
        # TODO Pseudo code:
        # if uri.scheme not in SupportedUriSchemes: return
        # if uri.mime_type not in SupportedMimeTypes: return
        # track = library.lookup(uri)
        # cp_track = current_playlist.add(track)
        # playback.play(cp_track)
        pass


    ### Player interface signals

    @dbus.service.signal(dbus_interface=PLAYER_IFACE, signature='x')
    def Seeked(self, position):
        logger.debug(u'%s.Seeked signaled', PLAYER_IFACE)
        # TODO What should we do here?
        pass


    ### Player interface properties

    def get_PlaybackStatus(self):
        state = self.backend.playback.state.get()
        if state == PlaybackController.PLAYING:
            return 'Playing'
        elif state == PlaybackController.PAUSED:
            return 'Paused'
        elif state == PlaybackController.STOPPED:
            return 'Stopped'

    def get_LoopStatus(self):
        repeat = self.backend.playback.repeat.get()
        single = self.backend.playback.single.get()
        if not repeat:
            return 'None'
        else:
            if single:
                return 'Track'
            else:
                return 'Playlist'

    def set_LoopStatus(self, value):
        if value == 'None':
            self.backend.playback.repeat = False
            self.backend.playback.single = False
        elif value == 'Track':
            self.backend.playback.repeat = True
            self.backend.playback.single = True
        elif value == 'Playlist':
            self.backend.playback.repeat = True
            self.backend.playback.single = False

    def set_Rate(self, value):
        if value == 0:
            self.Pause()

    def get_Shuffle(self):
        return self.backend.playback.shuffle.get()

    def set_Shuffle(self, value):
        if value:
            self.backend.playback.shuffle = True
        else:
            self.backend.playback.shuffle = False

    def get_Volume(self):
        volume = self.mixer.volume.get()
        if volume is not None:
            return volume / 100.0

    def set_Volume(self, value):
        if value is None:
            return
        elif value < 0:
            self.mixer.volume = 0
        elif value > 1:
            self.mixer.volume = 100
        elif 0 <= value <= 1:
            self.mixer.volume = int(value * 100)
