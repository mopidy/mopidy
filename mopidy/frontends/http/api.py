from mopidy import exceptions

try:
    import cherrypy
except ImportError as import_error:
    raise exceptions.OptionalDependencyError(import_error)


class ApiResource(object):
    exposed = True

    def __init__(self, core):
        self.core = core
        self.player = PlayerResource(core)
        self.tracklist = TrackListResource(core)
        self.playlists = PlaylistsResource(core)

    @cherrypy.tools.json_out()
    def GET(self):
        return {
            'resources': {
                'player': {
                    'href': '/api/player/',
                },
                'tracklist': {
                    'href': '/api/tracklist/',
                },
                'playlists': {
                    'href': '/api/playlists/',
                },
            }
        }


class PlayerResource(object):
    exposed = True

    def __init__(self, core):
        self.core = core

    @cherrypy.tools.json_out()
    def GET(self):
        futures = {
            'state': self.core.playback.state,
            'current_track': self.core.playback.current_track,
            'consume': self.core.playback.consume,
            'random': self.core.playback.random,
            'repeat': self.core.playback.repeat,
            'single': self.core.playback.single,
            'volume': self.core.playback.volume,
            'time_position': self.core.playback.time_position,
        }
        current_track = futures['current_track'].get()
        if current_track:
            current_track = current_track.serialize()
        return {
            'properties': {
                'state': futures['state'].get(),
                'currentTrack': current_track,
                'consume': futures['consume'].get(),
                'random': futures['random'].get(),
                'repeat': futures['repeat'].get(),
                'single': futures['single'].get(),
                'volume': futures['volume'].get(),
                'timePosition': futures['time_position'].get(),
            }
        }


class TrackListResource(object):
    exposed = True

    def __init__(self, core):
        self.core = core

    @cherrypy.tools.json_out()
    def GET(self):
        futures = {
            'cp_tracks': self.core.current_playlist.cp_tracks,
            'current_cp_track': self.core.playback.current_cp_track,
        }
        cp_tracks = futures['cp_tracks'].get()
        tracks = []
        for cp_track in cp_tracks:
            track = cp_track.track.serialize()
            track['cpid'] = cp_track.cpid
            tracks.append(track)
        current_cp_track = futures['current_cp_track'].get()
        return {
            'currentTrackCpid': current_cp_track and current_cp_track.cpid,
            'tracks': tracks,
        }


class PlaylistsResource(object):
    exposed = True

    def __init__(self, core):
        self.core = core

    @cherrypy.tools.json_out()
    def GET(self):
        playlists = self.core.stored_playlists.playlists.get()
        return {
            'playlists': [p.serialize() for p in playlists],
        }
