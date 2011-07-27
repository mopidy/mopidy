import logging

try:
    import dbus
    import dbus.mainloop.glib
    import dbus.service
except ImportError as import_error:
    from mopidy import OptionalDependencyError
    raise OptionalDependencyError(import_error)

from pykka.actor import ThreadingActor
from pykka.registry import ActorRegistry

from mopidy.backends.base import Backend
from mopidy.backends.base.playback import PlaybackController
from mopidy.listeners import BackendListener
from mopidy.mixers.base import BaseMixer
from mopidy.utils.process import exit_process

logger = logging.getLogger('mopidy.frontends.mpris')

# Must be done before dbus.SessionBus() is called
dbus.mainloop.glib.threads_init()
dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)

BUS_NAME = 'org.mpris.MediaPlayer2.mopidy'
OBJECT_PATH = '/org/mpris/MediaPlayer2'
ROOT_IFACE = 'org.mpris.MediaPlayer2'
PLAYER_IFACE = 'org.mpris.MediaPlayer2.Player'


class MprisFrontend(ThreadingActor, BackendListener):
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
        self.indicate_server = None
        self.mpris_object = None

    def on_start(self):
        self.mpris_object = MprisObject()
        self.send_startup_notification()

    def on_stop(self):
        logger.debug(u'Removing MPRIS object from D-Bus connection...')
        self.mpris_object.remove_from_connection()
        self.mpris_object = None
        logger.debug(u'Removed MPRIS object from D-Bus connection')

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
            logger.debug(u'Sending startup notification...')
            self.indicate_server = indicate.Server()
            self.indicate_server.set_type('music.mopidy')
            # FIXME Location of .desktop file shouldn't be hardcoded
            self.indicate_server.set_desktop_file(
                '/usr/share/applications/mopidy.desktop')
            self.indicate_server.show()
            logger.debug(u'Startup notification sent')
        except ImportError as e:
            logger.debug(u'Startup notification was not sent (%s)', e)

    def track_playback_paused(self, track, time_position):
        logger.debug(u'Received track playback paused event')
        if self.mpris_object is None:
            return
        self.mpris_object.PropertiesChanged(PLAYER_IFACE, {
            'PlaybackStatus':
                self.mpris_object.Get(PLAYER_IFACE, 'PlaybackStatus'),
        }, [])

    def track_playback_resumed(self, track, time_position):
        logger.debug(u'Received track playback resumed event')
        if self.mpris_object is None:
            return
        self.mpris_object.PropertiesChanged(PLAYER_IFACE, {
            'PlaybackStatus':
                self.mpris_object.Get(PLAYER_IFACE, 'PlaybackStatus'),
        }, [])

    def track_playback_started(self, track):
        logger.debug(u'Received track playback started event')
        if self.mpris_object is None:
            return
        self.mpris_object.PropertiesChanged(PLAYER_IFACE, {
            'Metadata': self.mpris_object.Get(PLAYER_IFACE, 'Metadata'),
            'PlaybackStatus':
                self.mpris_object.Get(PLAYER_IFACE, 'PlaybackStatus'),
        }, [])

    def track_playback_ended(self, track, time_position):
        logger.debug(u'Received track playback ended event')
        if self.mpris_object is None:
            return
        self.mpris_object.PropertiesChanged(PLAYER_IFACE, {
            'Metadata': self.mpris_object.Get(PLAYER_IFACE, 'Metadata'),
            'PlaybackStatus':
                self.mpris_object.Get(PLAYER_IFACE, 'PlaybackStatus'),
        }, [])

    def volume_changed(self):
        logger.debug(u'Received volume changed event')
        if self.mpris_object is None:
            return
        self.mpris_object.PropertiesChanged(PLAYER_IFACE, {
            'Volume': self.mpris_object.Get(PLAYER_IFACE, 'Volume'),
        }, [])

    def seeked(self):
        logger.debug(u'Received seeked event')
        if self.mpris_object is None:
            return
        self.mpris_object.Seeked(PLAYER_IFACE, self.mpris_object.Get(PLAYER_IFACE, 'Position'))


class MprisObject(dbus.service.Object):
    """Implements http://www.mpris.org/2.1/spec/"""

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
            # NOTE Change if adding optional track list support
            'HasTrackList': (False, None),
            'Identity': ('Mopidy', None),
            'DesktopEntry': ('mopidy', None),
            'SupportedUriSchemes': (self.get_SupportedUriSchemes, None),
            # TODO Return MIME types supported by local backend if active
            'SupportedMimeTypes': (dbus.Array([], signature='s'), None),
        }

    def _get_player_iface_properties(self):
        return {
            'PlaybackStatus': (self.get_PlaybackStatus, None),
            'LoopStatus': (self.get_LoopStatus, self.set_LoopStatus),
            'Rate': (1.0, self.set_Rate),
            'Shuffle': (self.get_Shuffle, self.set_Shuffle),
            'Metadata': (self.get_Metadata, None),
            'Volume': (self.get_Volume, self.set_Volume),
            'Position': (self.get_Position, None),
            'MinimumRate': (1.0, None),
            'MaximumRate': (1.0, None),
            'CanGoNext': (self.get_CanGoNext, None),
            'CanGoPrevious': (self.get_CanGoPrevious, None),
            'CanPlay': (self.get_CanPlay, None),
            'CanPause': (self.get_CanPause, None),
            'CanSeek': (self.get_CanSeek, None),
            'CanControl': (self.get_CanControl, None),
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

    def _get_track_id(self, cp_track):
        return '/com/mopidy/track/%d' % cp_track.cpid

    def _get_cpid(self, track_id):
        assert track_id.startswith('/com/mopidy/track/')
        return track_id.split('/')[-1]

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
        logger.debug(u'%s.PropertiesChanged(%s, %s, %s) signaled',
            dbus.PROPERTIES_IFACE, interface, changed_properties,
            invalidated_properties)


    ### Root interface methods

    @dbus.service.method(dbus_interface=ROOT_IFACE)
    def Raise(self):
        logger.debug(u'%s.Raise called', ROOT_IFACE)
        pass # We do not have a GUI

    @dbus.service.method(dbus_interface=ROOT_IFACE)
    def Quit(self):
        logger.debug(u'%s.Quit called', ROOT_IFACE)
        exit_process()


    ### Root interface properties

    def get_SupportedUriSchemes(self):
        return dbus.Array(self.backend.uri_schemes.get(), signature='s')


    ### Player interface methods

    @dbus.service.method(dbus_interface=PLAYER_IFACE)
    def Next(self):
        logger.debug(u'%s.Next called', PLAYER_IFACE)
        if not self.get_CanGoNext():
            logger.debug(u'%s.Next not allowed', PLAYER_IFACE)
            return
        self.backend.playback.next().get()

    @dbus.service.method(dbus_interface=PLAYER_IFACE)
    def Previous(self):
        logger.debug(u'%s.Previous called', PLAYER_IFACE)
        if not self.get_CanGoPrevious():
            logger.debug(u'%s.Previous not allowed', PLAYER_IFACE)
            return
        self.backend.playback.previous().get()

    @dbus.service.method(dbus_interface=PLAYER_IFACE)
    def Pause(self):
        logger.debug(u'%s.Pause called', PLAYER_IFACE)
        if not self.get_CanPause():
            logger.debug(u'%s.Pause not allowed', PLAYER_IFACE)
            return
        self.backend.playback.pause().get()

    @dbus.service.method(dbus_interface=PLAYER_IFACE)
    def PlayPause(self):
        logger.debug(u'%s.PlayPause called', PLAYER_IFACE)
        if not self.get_CanPause():
            logger.debug(u'%s.PlayPause not allowed', PLAYER_IFACE)
            return # TODO Raise error
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
        if not self.get_CanControl():
            logger.debug(u'%s.Stop not allowed', PLAYER_IFACE)
            return # TODO Raise error
        self.backend.playback.stop().get()

    @dbus.service.method(dbus_interface=PLAYER_IFACE)
    def Play(self):
        logger.debug(u'%s.Play called', PLAYER_IFACE)
        if not self.get_CanPlay():
            logger.debug(u'%s.Play not allowed', PLAYER_IFACE)
            return
        state = self.backend.playback.state.get()
        if state == PlaybackController.PAUSED:
            self.backend.playback.resume().get()
        else:
            self.backend.playback.play().get()

    @dbus.service.method(dbus_interface=PLAYER_IFACE)
    def Seek(self, offset):
        logger.debug(u'%s.Seek called', PLAYER_IFACE)
        if not self.get_CanSeek():
            logger.debug(u'%s.Seek not allowed', PLAYER_IFACE)
            return
        offset_in_milliseconds = offset // 1000
        current_position = self.backend.playback.time_position.get()
        new_position = current_position + offset_in_milliseconds
        self.backend.playback.seek(new_position)

    @dbus.service.method(dbus_interface=PLAYER_IFACE)
    def SetPosition(self, track_id, position):
        logger.debug(u'%s.SetPosition called', PLAYER_IFACE)
        if not self.get_CanSeek():
            logger.debug(u'%s.SetPosition not allowed', PLAYER_IFACE)
            return
        position = position // 1000
        current_cp_track = self.backend.playback.current_cp_track.get()
        if current_cp_track is None:
            return
        if track_id != self._get_track_id(current_cp_track):
            return
        if position < 0:
            return
        if current_cp_track.track.length < position:
            return
        self.backend.playback.seek(position)

    @dbus.service.method(dbus_interface=PLAYER_IFACE)
    def OpenUri(self, uri):
        logger.debug(u'%s.OpenUri called', PLAYER_IFACE)
        if not self.get_CanPlay():
            # NOTE The spec does not explictly require this check, but guarding
            # the other methods doesn't help much if OpenUri is open for use.
            logger.debug(u'%s.Play not allowed', PLAYER_IFACE)
            return
        # TODO Check if URI has known MIME type.
        uri_schemes = self.backend.uri_schemes.get()
        if not any([uri.startswith(uri_scheme) for uri_scheme in uri_schemes]):
            return
        track = self.backend.library.lookup(uri).get()
        if track is not None:
            cp_track = self.backend.current_playlist.add(track).get()
            self.backend.playback.play(cp_track)
        else:
            logger.debug(u'Track with URI "%s" not found in library.', uri)


    ### Player interface signals

    @dbus.service.signal(dbus_interface=PLAYER_IFACE, signature='x')
    def Seeked(self, position):
        logger.debug(u'%s.Seeked signaled', PLAYER_IFACE)
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
        if not self.get_CanControl():
            logger.debug(u'Setting %s.LoopStatus not allowed', PLAYER_IFACE)
            return # TODO Raise error
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
        if not self.get_CanControl():
            # NOTE The spec does not explictly require this check, but it was
            # added to be consistent with all the other property setters.
            logger.debug(u'Setting %s.Rate not allowed', PLAYER_IFACE)
            return # TODO Raise error
        if value == 0:
            self.Pause()

    def get_Shuffle(self):
        return self.backend.playback.random.get()

    def set_Shuffle(self, value):
        if not self.get_CanControl():
            logger.debug(u'Setting %s.Shuffle not allowed', PLAYER_IFACE)
            return # TODO Raise error
        if value:
            self.backend.playback.random = True
        else:
            self.backend.playback.random = False

    def get_Metadata(self):
        current_cp_track = self.backend.playback.current_cp_track.get()
        if current_cp_track is None:
            return {'mpris:trackid': ''}
        else:
            (cpid, track) = current_cp_track
            metadata = {'mpris:trackid': self._get_track_id(current_cp_track)}
            if track.length:
                metadata['mpris:length'] = track.length * 1000
            if track.uri:
                metadata['xesam:url'] = track.uri
            if track.name:
                metadata['xesam:title'] = track.name
            if track.artists:
                artists = list(track.artists)
                artists.sort(key=lambda a: a.name)
                metadata['xesam:artist'] = dbus.Array(
                    [a.name for a in artists if a.name], signature='s')
            if track.album and track.album.name:
                metadata['xesam:album'] = track.album.name
            if track.album and track.album.artists:
                artists = list(track.album.artists)
                artists.sort(key=lambda a: a.name)
                metadata['xesam:albumArtist'] = dbus.Array(
                    [a.name for a in artists if a.name], signature='s')
            if track.track_no:
                metadata['xesam:trackNumber'] = track.track_no
            return dbus.Dictionary(metadata, signature='sv')

    def get_Volume(self):
        volume = self.mixer.volume.get()
        if volume is not None:
            return volume / 100.0

    def set_Volume(self, value):
        if not self.get_CanControl():
            logger.debug(u'Setting %s.Volume not allowed', PLAYER_IFACE)
            return # TODO Raise error
        if value is None:
            return
        elif value < 0:
            self.mixer.volume = 0
        elif value > 1:
            self.mixer.volume = 100
        elif 0 <= value <= 1:
            self.mixer.volume = int(value * 100)

    def get_Position(self):
        return self.backend.playback.time_position.get() * 1000

    def get_CanGoNext(self):
        if not self.get_CanControl():
            return False
        return (self.backend.playback.cp_track_at_next.get() !=
            self.backend.playback.current_cp_track.get())

    def get_CanGoPrevious(self):
        if not self.get_CanControl():
            return False
        return (self.backend.playback.cp_track_at_previous.get() !=
            self.backend.playback.current_cp_track.get())

    def get_CanPlay(self):
        if not self.get_CanControl():
            return False
        return (self.backend.playback.current_track.get() is not None
            or self.backend.playback.track_at_next.get() is not None)

    def get_CanPause(self):
        if not self.get_CanControl():
            return False
        # NOTE Should be changed to vary based on capabilities of the current
        # track if Mopidy starts supporting non-seekable media, like streams.
        return True

    def get_CanSeek(self):
        if not self.get_CanControl():
            return False
        # NOTE Should be changed to vary based on capabilities of the current
        # track if Mopidy starts supporting non-seekable media, like streams.
        return True

    def get_CanControl(self):
        # NOTE This could be a setting for the end user to change.
        return True
