from __future__ import unicode_literals

import base64
import logging
import os

import dbus
import dbus.mainloop.glib
import dbus.service
import gobject

from mopidy.core import PlaybackState
from mopidy.utils.process import exit_process


logger = logging.getLogger('mopidy.frontends.mpris')

# Must be done before dbus.SessionBus() is called
gobject.threads_init()
dbus.mainloop.glib.threads_init()

BUS_NAME = 'org.mpris.MediaPlayer2.mopidy'
OBJECT_PATH = '/org/mpris/MediaPlayer2'
ROOT_IFACE = 'org.mpris.MediaPlayer2'
PLAYER_IFACE = 'org.mpris.MediaPlayer2.Player'
PLAYLISTS_IFACE = 'org.mpris.MediaPlayer2.Playlists'


class MprisObject(dbus.service.Object):
    """Implements http://www.mpris.org/2.2/spec/"""

    properties = None

    def __init__(self, config, core):
        self.config = config
        self.core = core
        self.properties = {
            ROOT_IFACE: self._get_root_iface_properties(),
            PLAYER_IFACE: self._get_player_iface_properties(),
            PLAYLISTS_IFACE: self._get_playlists_iface_properties(),
        }
        bus_name = self._connect_to_dbus()
        dbus.service.Object.__init__(self, bus_name, OBJECT_PATH)

    def _get_root_iface_properties(self):
        return {
            'CanQuit': (True, None),
            'Fullscreen': (False, None),
            'CanSetFullscreen': (False, None),
            'CanRaise': (False, None),
            # NOTE Change if adding optional track list support
            'HasTrackList': (False, None),
            'Identity': ('Mopidy', None),
            'DesktopEntry': (self.get_DesktopEntry, None),
            'SupportedUriSchemes': (self.get_SupportedUriSchemes, None),
            # NOTE Return MIME types supported by local backend if support for
            # reporting supported MIME types is added
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

    def _get_playlists_iface_properties(self):
        return {
            'PlaylistCount': (self.get_PlaylistCount, None),
            'Orderings': (self.get_Orderings, None),
            'ActivePlaylist': (self.get_ActivePlaylist, None),
        }

    def _connect_to_dbus(self):
        logger.debug('Connecting to D-Bus...')
        mainloop = dbus.mainloop.glib.DBusGMainLoop()
        bus_name = dbus.service.BusName(
            BUS_NAME, dbus.SessionBus(mainloop=mainloop))
        logger.info('MPRIS server connected to D-Bus')
        return bus_name

    def get_playlist_id(self, playlist_uri):
        # Only A-Za-z0-9_ is allowed, which is 63 chars, so we can't use
        # base64. Luckily, D-Bus does not limit the length of object paths.
        # Since base32 pads trailing bytes with "=" chars, we need to replace
        # them with an allowed character such as "_".
        encoded_uri = base64.b32encode(playlist_uri).replace('=', '_')
        return '/com/mopidy/playlist/%s' % encoded_uri

    def get_playlist_uri(self, playlist_id):
        encoded_uri = playlist_id.split('/')[-1].replace('_', '=')
        return base64.b32decode(encoded_uri)

    def get_track_id(self, tl_track):
        return '/com/mopidy/track/%d' % tl_track.tlid

    def get_track_tlid(self, track_id):
        assert track_id.startswith('/com/mopidy/track/')
        return track_id.split('/')[-1]

    ### Properties interface

    @dbus.service.method(dbus_interface=dbus.PROPERTIES_IFACE,
                         in_signature='ss', out_signature='v')
    def Get(self, interface, prop):
        logger.debug(
            '%s.Get(%s, %s) called',
            dbus.PROPERTIES_IFACE, repr(interface), repr(prop))
        (getter, _) = self.properties[interface][prop]
        if callable(getter):
            return getter()
        else:
            return getter

    @dbus.service.method(dbus_interface=dbus.PROPERTIES_IFACE,
                         in_signature='s', out_signature='a{sv}')
    def GetAll(self, interface):
        logger.debug(
            '%s.GetAll(%s) called', dbus.PROPERTIES_IFACE, repr(interface))
        getters = {}
        for key, (getter, _) in self.properties[interface].iteritems():
            getters[key] = getter() if callable(getter) else getter
        return getters

    @dbus.service.method(dbus_interface=dbus.PROPERTIES_IFACE,
                         in_signature='ssv', out_signature='')
    def Set(self, interface, prop, value):
        logger.debug(
            '%s.Set(%s, %s, %s) called',
            dbus.PROPERTIES_IFACE, repr(interface), repr(prop), repr(value))
        _, setter = self.properties[interface][prop]
        if setter is not None:
            setter(value)
            self.PropertiesChanged(
                interface, {prop: self.Get(interface, prop)}, [])

    @dbus.service.signal(dbus_interface=dbus.PROPERTIES_IFACE,
                         signature='sa{sv}as')
    def PropertiesChanged(self, interface, changed_properties,
                          invalidated_properties):
        logger.debug(
            '%s.PropertiesChanged(%s, %s, %s) signaled',
            dbus.PROPERTIES_IFACE, interface, changed_properties,
            invalidated_properties)

    ### Root interface methods

    @dbus.service.method(dbus_interface=ROOT_IFACE)
    def Raise(self):
        logger.debug('%s.Raise called', ROOT_IFACE)
        # Do nothing, as we do not have a GUI

    @dbus.service.method(dbus_interface=ROOT_IFACE)
    def Quit(self):
        logger.debug('%s.Quit called', ROOT_IFACE)
        exit_process()

    ### Root interface properties

    def get_DesktopEntry(self):
        return os.path.splitext(os.path.basename(
            self.config['mpris']['desktop_file']))[0]

    def get_SupportedUriSchemes(self):
        return dbus.Array(self.core.uri_schemes.get(), signature='s')

    ### Player interface methods

    @dbus.service.method(dbus_interface=PLAYER_IFACE)
    def Next(self):
        logger.debug('%s.Next called', PLAYER_IFACE)
        if not self.get_CanGoNext():
            logger.debug('%s.Next not allowed', PLAYER_IFACE)
            return
        self.core.playback.next().get()

    @dbus.service.method(dbus_interface=PLAYER_IFACE)
    def Previous(self):
        logger.debug('%s.Previous called', PLAYER_IFACE)
        if not self.get_CanGoPrevious():
            logger.debug('%s.Previous not allowed', PLAYER_IFACE)
            return
        self.core.playback.previous().get()

    @dbus.service.method(dbus_interface=PLAYER_IFACE)
    def Pause(self):
        logger.debug('%s.Pause called', PLAYER_IFACE)
        if not self.get_CanPause():
            logger.debug('%s.Pause not allowed', PLAYER_IFACE)
            return
        self.core.playback.pause().get()

    @dbus.service.method(dbus_interface=PLAYER_IFACE)
    def PlayPause(self):
        logger.debug('%s.PlayPause called', PLAYER_IFACE)
        if not self.get_CanPause():
            logger.debug('%s.PlayPause not allowed', PLAYER_IFACE)
            return
        state = self.core.playback.state.get()
        if state == PlaybackState.PLAYING:
            self.core.playback.pause().get()
        elif state == PlaybackState.PAUSED:
            self.core.playback.resume().get()
        elif state == PlaybackState.STOPPED:
            self.core.playback.play().get()

    @dbus.service.method(dbus_interface=PLAYER_IFACE)
    def Stop(self):
        logger.debug('%s.Stop called', PLAYER_IFACE)
        if not self.get_CanControl():
            logger.debug('%s.Stop not allowed', PLAYER_IFACE)
            return
        self.core.playback.stop().get()

    @dbus.service.method(dbus_interface=PLAYER_IFACE)
    def Play(self):
        logger.debug('%s.Play called', PLAYER_IFACE)
        if not self.get_CanPlay():
            logger.debug('%s.Play not allowed', PLAYER_IFACE)
            return
        state = self.core.playback.state.get()
        if state == PlaybackState.PAUSED:
            self.core.playback.resume().get()
        else:
            self.core.playback.play().get()

    @dbus.service.method(dbus_interface=PLAYER_IFACE)
    def Seek(self, offset):
        logger.debug('%s.Seek called', PLAYER_IFACE)
        if not self.get_CanSeek():
            logger.debug('%s.Seek not allowed', PLAYER_IFACE)
            return
        offset_in_milliseconds = offset // 1000
        current_position = self.core.playback.time_position.get()
        new_position = current_position + offset_in_milliseconds
        self.core.playback.seek(new_position)

    @dbus.service.method(dbus_interface=PLAYER_IFACE)
    def SetPosition(self, track_id, position):
        logger.debug('%s.SetPosition called', PLAYER_IFACE)
        if not self.get_CanSeek():
            logger.debug('%s.SetPosition not allowed', PLAYER_IFACE)
            return
        position = position // 1000
        current_tl_track = self.core.playback.current_tl_track.get()
        if current_tl_track is None:
            return
        if track_id != self.get_track_id(current_tl_track):
            return
        if position < 0:
            return
        if current_tl_track.track.length < position:
            return
        self.core.playback.seek(position)

    @dbus.service.method(dbus_interface=PLAYER_IFACE)
    def OpenUri(self, uri):
        logger.debug('%s.OpenUri called', PLAYER_IFACE)
        if not self.get_CanPlay():
            # NOTE The spec does not explictly require this check, but guarding
            # the other methods doesn't help much if OpenUri is open for use.
            logger.debug('%s.Play not allowed', PLAYER_IFACE)
            return
        # NOTE Check if URI has MIME type known to the backend, if MIME support
        # is added to the backend.
        tl_tracks = self.core.tracklist.add(uri=uri).get()
        if tl_tracks:
            self.core.playback.play(tl_tracks[0])
        else:
            logger.debug('Track with URI "%s" not found in library.', uri)

    ### Player interface signals

    @dbus.service.signal(dbus_interface=PLAYER_IFACE, signature='x')
    def Seeked(self, position):
        logger.debug('%s.Seeked signaled', PLAYER_IFACE)
        # Do nothing, as just calling the method is enough to emit the signal.

    ### Player interface properties

    def get_PlaybackStatus(self):
        state = self.core.playback.state.get()
        if state == PlaybackState.PLAYING:
            return 'Playing'
        elif state == PlaybackState.PAUSED:
            return 'Paused'
        elif state == PlaybackState.STOPPED:
            return 'Stopped'

    def get_LoopStatus(self):
        repeat = self.core.playback.repeat.get()
        single = self.core.playback.single.get()
        if not repeat:
            return 'None'
        else:
            if single:
                return 'Track'
            else:
                return 'Playlist'

    def set_LoopStatus(self, value):
        if not self.get_CanControl():
            logger.debug('Setting %s.LoopStatus not allowed', PLAYER_IFACE)
            return
        if value == 'None':
            self.core.playback.repeat = False
            self.core.playback.single = False
        elif value == 'Track':
            self.core.playback.repeat = True
            self.core.playback.single = True
        elif value == 'Playlist':
            self.core.playback.repeat = True
            self.core.playback.single = False

    def set_Rate(self, value):
        if not self.get_CanControl():
            # NOTE The spec does not explictly require this check, but it was
            # added to be consistent with all the other property setters.
            logger.debug('Setting %s.Rate not allowed', PLAYER_IFACE)
            return
        if value == 0:
            self.Pause()

    def get_Shuffle(self):
        return self.core.playback.random.get()

    def set_Shuffle(self, value):
        if not self.get_CanControl():
            logger.debug('Setting %s.Shuffle not allowed', PLAYER_IFACE)
            return
        if value:
            self.core.playback.random = True
        else:
            self.core.playback.random = False

    def get_Metadata(self):
        current_tl_track = self.core.playback.current_tl_track.get()
        if current_tl_track is None:
            return {'mpris:trackid': ''}
        else:
            (_, track) = current_tl_track
            metadata = {'mpris:trackid': self.get_track_id(current_tl_track)}
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
            if track.album and track.album.images:
                url = list(track.album.images)[0]
                if url:
                    metadata['mpris:artUrl'] = url
            if track.disc_no:
                metadata['xesam:discNumber'] = track.disc_no
            if track.track_no:
                metadata['xesam:trackNumber'] = track.track_no
            return dbus.Dictionary(metadata, signature='sv')

    def get_Volume(self):
        volume = self.core.playback.volume.get()
        if volume is None:
            return 0
        return volume / 100.0

    def set_Volume(self, value):
        if not self.get_CanControl():
            logger.debug('Setting %s.Volume not allowed', PLAYER_IFACE)
            return
        if value is None:
            return
        elif value < 0:
            self.core.playback.volume = 0
        elif value > 1:
            self.core.playback.volume = 100
        elif 0 <= value <= 1:
            self.core.playback.volume = int(value * 100)

    def get_Position(self):
        return self.core.playback.time_position.get() * 1000

    def get_CanGoNext(self):
        if not self.get_CanControl():
            return False
        return (
            self.core.playback.tl_track_at_next.get() !=
            self.core.playback.current_tl_track.get())

    def get_CanGoPrevious(self):
        if not self.get_CanControl():
            return False
        return (
            self.core.playback.tl_track_at_previous.get() !=
            self.core.playback.current_tl_track.get())

    def get_CanPlay(self):
        if not self.get_CanControl():
            return False
        return (
            self.core.playback.current_tl_track.get() is not None or
            self.core.playback.tl_track_at_next.get() is not None)

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

    ### Playlists interface methods

    @dbus.service.method(dbus_interface=PLAYLISTS_IFACE)
    def ActivatePlaylist(self, playlist_id):
        logger.debug(
            '%s.ActivatePlaylist(%r) called', PLAYLISTS_IFACE, playlist_id)
        playlist_uri = self.get_playlist_uri(playlist_id)
        playlist = self.core.playlists.lookup(playlist_uri).get()
        if playlist and playlist.tracks:
            tl_tracks = self.core.tracklist.add(playlist.tracks).get()
            self.core.playback.play(tl_tracks[0])

    @dbus.service.method(dbus_interface=PLAYLISTS_IFACE)
    def GetPlaylists(self, index, max_count, order, reverse):
        logger.debug(
            '%s.GetPlaylists(%r, %r, %r, %r) called',
            PLAYLISTS_IFACE, index, max_count, order, reverse)
        playlists = self.core.playlists.playlists.get()
        if order == 'Alphabetical':
            playlists.sort(key=lambda p: p.name, reverse=reverse)
        elif order == 'Modified':
            playlists.sort(key=lambda p: p.last_modified, reverse=reverse)
        elif order == 'User' and reverse:
            playlists.reverse()
        slice_end = index + max_count
        playlists = playlists[index:slice_end]
        results = [
            (self.get_playlist_id(p.uri), p.name, '')
            for p in playlists]
        return dbus.Array(results, signature='(oss)')

    ### Playlists interface signals

    @dbus.service.signal(dbus_interface=PLAYLISTS_IFACE, signature='(oss)')
    def PlaylistChanged(self, playlist):
        logger.debug('%s.PlaylistChanged signaled', PLAYLISTS_IFACE)
        # Do nothing, as just calling the method is enough to emit the signal.

    ### Playlists interface properties

    def get_PlaylistCount(self):
        return len(self.core.playlists.playlists.get())

    def get_Orderings(self):
        return [
            'Alphabetical',  # Order by playlist.name
            'Modified',      # Order by playlist.last_modified
            'User',          # Don't change order
        ]

    def get_ActivePlaylist(self):
        playlist_is_valid = False
        playlist = ('/', 'None', '')
        return (playlist_is_valid, playlist)
