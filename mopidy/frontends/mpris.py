import logging
import multiprocessing

try:
    import dbus
    import dbus.service
    from dbus.mainloop.glib import DBusGMainLoop, threads_init
    threads_init()
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

    An example of an MPRIS client is `Ubuntu's sound menu
    <https://wiki.ubuntu.com/SoundMenu>`_.

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
    """
    A process for communicating with MPRIS clients.

    This thread requires :class:`mopidy.utils.process.GObjectEventThread` to be
    running too. This is not enforced in any way by the code.
    """

    def __init__(self, core_queue, connection):
        super(MprisFrontendThread, self).__init__(core_queue)
        self.name = u'MprisFrontendThread'
        self.connection = connection
        self.indicate_server = None
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
        self.send_startup_notification()

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
                '/usr/local/share/applications/mopidy.desktop')
            self.indicate_server.show()
        except ImportError:
            pass

    def process_message(self, message):
        pass # Ignore commands for other frontends


class MprisObject(dbus.service.Object):
    """Implements http://www.mpris.org/2.0/spec/"""

    bus_name = 'org.mpris.MediaPlayer2.mopidy'
    object_path = '/org/mpris/MediaPlayer2'
    properties_interface = 'org.freedesktop.DBus.Properties'
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
            'SupportedUriSchemes': (dbus.Array([], signature='s'), None),
            # TODO Return MIME types supported by local backend if active
            'SupportedMimeTypes': (dbus.Array([], signature='s'), None),
        },
        player_interface: {
            # TODO Get backend.playback.state
            'PlaybackStatus': ('Stopped', None),
            # TODO Get/set loop status
            'LoopStatus': ('None', None),
            'Rate': (1.0, None),
            # TODO Get/set backend.playback.random
            'Shuffle': (False, None),
            # TODO Get meta data
            'Metadata': ({
                'mpris:trackid': '', # TODO Use (cpid, track.uri)
            }, None),
            # TODO Get/set volume
            'Volume': (1.0, None),
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
        },
    }

    def __init__(self, core_queue):
        self.core_queue = core_queue
        logger.debug(u'Prepare the D-Bus main loop before connecting')
        DBusGMainLoop(set_as_default=True)
        logger.debug(u'Connecting to D-Bus: getting session bus')
        bus = dbus.SessionBus()
        logger.debug(u'Connecting to D-Bus: claiming service name')
        # FIXME We segfault at the next line 80% of the time
        bus_name = dbus.service.BusName(self.bus_name, bus)
        logger.debug(u'Connecting to D-Bus: registering service object')
        super(MprisObject, self).__init__(object_path=self.object_path,
            bus_name=bus_name)
        logger.info(u'Connected to D-Bus')


    ### Property interface

    @dbus.service.method(dbus_interface=properties_interface,
        in_signature='ss', out_signature='v')
    def Get(self, interface, prop):
        logger.debug(u'%s.Get called', self.properties_interface)
        getter, setter = self.properties[interface][prop]
        return getter() if callable(getter) else getter

    @dbus.service.method(dbus_interface=properties_interface,
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
        logger.debug(u'%s.GetAll called', self.properties_interface)
        getters = {}
        for key, (getter, setter) in self.properties[interface].iteritems():
            getters[key] = getter() if callable(getter) else getter
        return getters

    @dbus.service.method(dbus_interface=properties_interface,
        in_signature='ssv', out_signature='')
    def Set(self, interface, prop, value):
        logger.debug(u'%s.Set called', self.properties_interface)
        getter, setter = self.properties[interface][prop]
        if setter is not None:
            setter(value)
            self.PropertiesChanged(interface,
                {prop: self.Get(interface, prop)}, [])

    @dbus.service.signal(dbus_interface=properties_interface,
            signature='sa{sv}as')
    def PropertiesChanged(self, interface, changed_properties,
        invalidated_properties):
        logger.debug(u'%s.PropertiesChanged signaled',
            self.properties_interface)
        pass


    ### Root interface

    @dbus.service.method(dbus_interface=root_interface)
    def Raise(self):
        logger.debug(u'%s.Raise called', self.root_interface)
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
        logger.debug(u'%s.Quit called', self.root_interface)
        self.core_queue.put({'to': 'core', 'command': 'exit'})


    ### Player interface

    @dbus.service.method(dbus_interface=player_interface)
    def Next(self):
        logger.debug(u'%s.Next called', self.player_interface)
        # TODO call playback.next(), keep playback.state unchanged
        pass

        # XXX Proof of concept only. Throw away, write tests, reimplement:
        self.core_queue.put({
            'to': 'frontend',
            'command': 'mpd_request',
            'request': 'next',
        })

    @dbus.service.method(dbus_interface=player_interface)
    def OpenUri(self, uri):
        logger.debug(u'%s.OpenUri called', self.player_interface)
        # TODO Pseudo code:
        # if uri.scheme not in SupportedUriSchemes: return
        # if uri.mime_type not in SupportedMimeTypes: return
        # track = library.lookup(uri)
        # cp_track = current_playlist.add(track)
        # playback.play(cp_track)
        pass

    @dbus.service.method(dbus_interface=player_interface)
    def Pause(self):
        logger.debug(u'%s.Pause called', self.player_interface)
        # TODO call playback.pause()
        pass

    @dbus.service.method(dbus_interface=player_interface)
    def Play(self):
        logger.debug(u'%s.Play called', self.player_interface)
        # TODO Pseudo code:
        # if playback.state == playback.PAUSED: playback.resume()
        # elif playback.state == playback.STOPPED: playback.play()
        pass

    @dbus.service.method(dbus_interface=player_interface)
    def PlayPause(self):
        logger.debug(u'%s.PlayPause called', self.player_interface)

        # TODO Pseudo code:
        # if playback.state == playback.PLAYING: playback.pause()
        # elif playback.state == playback.PAUSED: playback.resume()
        # elif playback.state == playback.STOPPED: playback.play()

        # XXX Proof of concept only. Throw away, write tests, reimplement:
        self.core_queue.put({
            'to': 'frontend',
            'command': 'mpd_request',
            'request': 'play',
        })

    @dbus.service.method(dbus_interface=player_interface)
    def Previous(self):
        logger.debug(u'%s.Previous called', self.player_interface)

        # TODO call playback.previous(), keep playback.state unchanged

        # XXX Proof of concept only. Throw away, write tests, reimplement:
        self.core_queue.put({
            'to': 'frontend',
            'command': 'mpd_request',
            'request': 'previous',
        })

    @dbus.service.method(dbus_interface=player_interface)
    def Seek(self, offset):
        logger.debug(u'%s.Seek called', self.player_interface)
        # TODO Pseudo code:
        # new_position = playback.time_position + offset
        # if new_position > playback.current_track.length:
        #     playback.next()
        #     return
        # if new_position < 0: new_position = 0
        # playback.seek(new_position)
        pass

    @dbus.service.method(dbus_interface=player_interface)
    def SetPosition(self, track_id, position):
        logger.debug(u'%s.SetPosition called', self.player_interface)
        # TODO Pseudo code:
        # if track_id != playback.current_track.track_id: return
        # if not 0 <= position <= playback.current_track.length: return
        # playback.seek(position)
        pass

    @dbus.service.method(dbus_interface=player_interface)
    def Stop(self):
        logger.debug(u'%s.Stop called', self.player_interface)
        # TODO call playback.stop()
        pass

    @dbus.service.signal(dbus_interface=player_interface, signature='x')
    def Seeked(self, position):
        logger.debug(u'%s.Seeked signaled', self.player_interface)
        pass
