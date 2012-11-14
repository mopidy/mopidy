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
        tl_tracks_future = self.core.tracklist.tl_tracks
        current_tl_track_future = self.core.playback.current_tl_track
        tracks = []
        for tl_track in tl_tracks_future.get():
            track = tl_track.track.serialize()
            track['tlid'] = tl_track.tlid
            tracks.append(track)
        current_tl_track = current_tl_track_future.get()
        return {
            'currentTrackTlid': current_tl_track and current_tl_track.tlid,
            'tracks': tracks,
        }


class PlaylistsResource(object):
    exposed = True

    def __init__(self, core):
        self.core = core

    @cherrypy.tools.json_out()
    def GET(self):
        playlists = self.core.playlists.playlists.get()
        return {
            'playlists': [p.serialize() for p in playlists],
        }
