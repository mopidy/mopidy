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
        properties = {
            'state': self.core.playback.state,
            'currentTrack': self.core.playback.current_track,
            'consume': self.core.playback.consume,
            'random': self.core.playback.random,
            'repeat': self.core.playback.repeat,
            'single': self.core.playback.single,
            'volume': self.core.playback.volume,
            'timePosition': self.core.playback.time_position,
        }
        for key, value in properties.items():
            properties[key] = value.get()
        if properties['currentTrack']:
            properties['currentTrack'] = properties['currentTrack'].serialize()
        return {'properties': properties}


class TrackListResource(object):
    exposed = True

    def __init__(self, core):
        self.core = core

    @cherrypy.tools.json_out()
    def GET(self):
        cp_tracks_future = self.core.current_playlist.cp_tracks
        current_cp_track_future = self.core.playback.current_cp_track
        tracks = []
        for cp_track in cp_tracks_future.get():
            track = cp_track.track.serialize()
            track['cpid'] = cp_track.cpid
            tracks.append(track)
        current_cp_track = current_cp_track_future.get()
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
