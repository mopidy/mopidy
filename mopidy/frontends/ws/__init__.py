"""
The WebSockets frontend.
based on mpd-frontend and examples from gevent-socketio
"""
import datetime as dt
import logging
import os
import sys

from socketio import socketio_manage
from socketio.server import SocketIOServer
from socketio.namespace import BaseNamespace
import socketio

from pykka import registry, actor

from mopidy import listeners, settings
from mopidy.utils import network, process, log

from mopidy.backends.base import Backend
from mopidy.mixers.base import BaseMixer
from mopidy.listeners import BackendListener
from mopidy.backends.base import PlaybackController
from mopidy.models import Playlist

#get directory with static web content
webdir = os.path.join(os.path.dirname(__file__), 'web')
logger = logging.getLogger('mopidy.frontends.ws')

#server object
srv = None

mutevolume = -1

def flattentracks(tracks):
    flattracks = []
    for track in tracks:
        flattrack = {}
        flatartists = []
        for artist in track.artists:
            flatartist = {}
            flatartist["name"] = artist.name
            flatartist["uri"] = artist.uri
            flatartists.append(flatartist)
            #flatartist.clear() 

        #flattrack["bitrate"] = track.bitrate
        flattrack["uri"] = track.uri
        flattrack["name"] = track.name
        flattrack["track_no"] = track.track_no
        flattrack["uri"] = track.uri
        flattrack["length"] = track.length / 1000
        flattrack["albumname"] = track.album.name
        flattrack["albumuri"] = track.album.uri
        flattrack["artists"] = flatartists
        flattracks.append(flattrack)
    return flattracks

def flattenplaylist(playlist):
    """ example playlist mopidy
    [   Track(
        album=Album(artists=[], name=u'Rachmaninov'), 
        artists=[Artist(name=u'Polish National Radio Symphony Orchestra', uri='spotify:artist:62QURushyB5wug2XPwajwK'), 
            Artist(name=u'Bernd Glemser', uri='spotify:artist:0OCB739kEu37yjT5VBLPEW'), Artist(name=u'Sergei Rachmaninov', 
                uri='spotify:artist:43X0PdXBooh9EBeGCy9iUk')], 
        bitrate=320, 
        date=datetime.date(2005, 1, 1), 
        length=666000, 
        name=u'Piano Concerto No. 2 In C Minor, Op. 18: Piano Concerto No. 2 In C Minor, Op. 18: II. Adagio Sostenuto', 
        track_no=1, 
        uri='spotify:track:3DouhiVMPEDinzcguT3I24'),
    """
    #for use with json
    #logger.info(playlist)


    result = dict({'name': playlist.name, 'uri': playlist.uri, 'tracks': flattentracks(playlist.tracks)})
    #pp = pprint.PrettyPrinter(indent=4)
    #pp.pprint(result)
    return result

def not_found(start_response):
    start_response('404 Not Found', [])
    return ['<h1>Not Found</h1>']

class WsNamespace(BaseNamespace):
    """

    Namespace for Gevent webserver 

    """

    #events from the client(s)
    def on_play(self, message=None):
        logger.info(' play')
        self.emit('status_change', message)
        if message:
            return self.request.backend.playback.play().get()
        else:
            return self.request.backend.playback.pause().get()
            
    def on_playtrack(self, trackuri):
        logger.info('play ' + trackuri)
        
        #try:
        logger.info(self.request.backend.playback.current_playlist_position.get())
        #cp_track = context.backend.current_playlist.get(cpid=cpid).get()
        #return context.backend.playback.play(cp_track).get()
        cp_track = self.request.backend.current_playlist.get(uri=trackuri).get()
        self.request.backend.playback.change_track(cp_track)
        
        logger.info(self.request.backend.playback.current_playlist_position.get())

        ####????
        logger.info(self.request.backend.playback.track_at_eot.get())
        
        return self.request.backend.playback.play().get()
        
        
        #except LookupError:
        #    pass
        #raise WsNoExistError(u'No such song', command=u'playid')
           
    def on_loadtracklist(self, trackuris):
        trackslist = []
        for uri in trackuris:
            track = self.request.backend.library.lookup(uri=uri).get()
            trackslist.append(track)
        
        playlist = Playlist(tracks=trackslist)
        self.request.backend.current_playlist.clear()
        res = self.request.backend.current_playlist.append(playlist.tracks).get()
        logger.info(res)
        
    def on_playplaylist(self, playuri):
        #TODO 
        logger.info(playuri)
        playlist = self.request.backend.stored_playlists.get(uri=playuri).get()
        self.request.backend.current_playlist.clear()
        res = self.request.backend.current_playlist.append(playlist.tracks).get()
        logger.info(res)
         
    def on_next(self, message=None):
        logger.info(' next')
        self.emit('status_change', 'next')
        self.request.backend.playback.next()
        
    def on_previous(self, message=None):
        self.emit('status_change', 'previous')
        self.request.backend.playback.previous()
        
    def on_stop(self, message=None):
        self.request.backend.playback.stop()
        
    def on_random(self, message=None):
        if message == 'true':
            self.request.backend.playback.random = True
        else:
            self.request.backend.playback.random = False
            
    def on_repeat(self, message=None):
        if message == 'true':
            self.request.backend.playback.repeat = True
        else:
            self.request.backend.playback.repeat = False
            
    def on_setvolume(self, volume):
        mutevolume = 0
        volume = int(volume)
        if volume < 0:
            volume = 0
        if volume > 100:
            volume = 100
        self.request.mixer.volume = volume
    
    def on_mute(self, state):
        #TODO Broadcast
        global mutevolume
        if state:
            logger.info('mute')
            mutevolume = int(self.request.mixer.volume.get())
            self.request.mixer.volume = 0
        elif mutevolume > 0:
            logger.info('unmute')
            self.request.mixer.volume = mutevolume
            mutevolume = -1
            
    def on_seek(self, message=None):
        pos = int(message)
        if (pos >= 0) and (pos <= 100000000): #100 mln sec should be enough 
            self.request.backend.playback.seek(int(seconds) * 1000)

    """
    context.backend.playback.random = True
    context.backend.playback.repeat = True
    context.mixer.volume = volume 1-100
    context.backend.playback.stop()
    context.backend.playback.consume = True
    cp_track = context.backend.current_playlist.slice(
            songpos, songpos + 1).get()[0]
        return context.backend.playback.play(cp_track).get()
    if context.backend.playback.current_playlist_position != songpos:
        playpos(context, songpos)
    context.backend.playback.seek(int(seconds) * 1000)
    """    
    
    #playlist handlers
    def on_getplaylists(self):
        result = []
        for playlist in self.request.backend.stored_playlists.playlists.get():
            last_modified = (playlist.last_modified or
                dt.datetime.now()).isoformat()
            # Add time zone information
            # TODO Convert to UTC before adding Z
            last_modified = last_modified + 'Z'
            result.append((playlist.name, playlist.uri, last_modified))
        self.emit('playlists', result)

    def on_getplaylisttracks(self, playlisturi):
        playlist = flattenplaylist(self.request.backend.stored_playlists.get(uri=playlisturi).get())
        self.emit('playlist', playlist)
    
    def on_search(self, searchtype, keywords):
        logger.info(searchtype + ':' + keywords)
        if searchtype == 'all':
            query = {'': keywords}
        else:
            query = {searchtype: keywords}
        playlist = flattenplaylist(self.request.backend.library.search(**query).get())
        logger.info(playlist)
         #context.backend.library.find_exact(**query).get())
        self.emit('searchresults', searchtype, playlist)

    def on_getalbum(self, albumuri):
        playlist = self.request.backend.library.lookup(uri=albumuri).get()
        logger.info(playlist)
        playlist = flattenplaylist(playlist)
        self.emit('albumresults', playlist)

    def on_getartist(self, artisturi):
        playlist = self.request.backend.library.lookup(uri=artisturi).get()
        logger.info(playlist)
        playlist = flattenplaylist(playlist)
        self.emit('artistresults', playlist)

    def on_getcurrentplaylist(self):
        #playlist = flattenplaylist(self.request.backend.current_playlist.get().get())
        playlist = flattentracks(self.request.backend.current_playlist.tracks.get())
        
        self.emit('currentplaylist', playlist)

   
class WsSession(object):
    """
    greenlet?
    
    Handles File-serving, mopidy events, passes WebSockets to namespace

    """
    def __init__(self):
        logger.info('wssession init')
        self.context = WsContext(self)
        
    def __call__(self, environ, start_response):
        logger.info('wssession call')
        os.chdir(webdir)
        logger.info(u'call webdir = ' + webdir)
        path = environ['PATH_INFO'].strip('/') or 'index.html'
        logger.info(' path = '  + path)
        if path.startswith('static/') or path.startswith('js/') or path.startswith('img/') or path.startswith('css/') or path == 'index.html':
            try:
                data = open(path).read()
            except Exception:
                return not_found(start_response)

            if path.endswith(".js"):
                content_type = "text/javascript"
            elif path.endswith(".png"):
                content_type = "image/png"
            elif path.endswith(".jpg"):
                content_type = "image/jpg"
            elif path.endswith(".ico"):
                content_type = "image/ico"
            elif path.endswith(".gif"):
                content_type = "image/gif"
            elif path.endswith(".css"):
                content_type = "text/css"
            elif path.endswith(".swf"):
                content_type = "application/x-shockwave-flash"
            else:
                content_type = "text/html"

            start_response('200 OK', [('Content-Type', content_type)])
            return [data]

        if path.startswith("socket.io"):
            #logger.info('socetio. envi: ' + str(environ))
            socketio_manage(environ, {'/mopidy': WsNamespace}, self.context)
        else:
            return not_found(start_response)

class WsFrontend(actor.ThreadingActor, listeners.BackendListener):
    """
    The WebSockets frontend.

    **Dependencies:**

    - gevent-socketio

    **Settings:**

    - :attr:`mopidy.settings.WS_SERVER_HOSTNAME`
    - :attr:`mopidy.settings.WS_SERVER_PORT`
    """

 
    def __init__(self):
        global srv
        super(WsFrontend, self).__init__()
        hostname = network.format_hostname(settings.WS_SERVER_HOSTNAME)
        port = settings.WS_SERVER_PORT
        
        try:
            srv = SocketIOServer((hostname, port), WsSession(), resource="socket.io", policy_server=True, policy_listener=(hostname, 10843)).serve_forever()
            #srv = SocketIOServer((hostname, port), WsSession(), resource="socket.io", policy_server=True, policy_listener=(hostname, 10843))
            #srv.start()
            SocketIOServer.spawn()
            logger.info(u'Websockets server running at [%s]:%s and on port 10843 (flash policy server)', hostname, port)
        except IOError, e:
            logger.error(u'Websockets server startup failed: %s', e)
            sys.exit(1)

    def on_stop(self):
        srv.stop()
        process.stop_actors_by_class(WsSession)

    #mopidy events
    def playback_state_changed(self):
        logger.info('playback state changed')
        self.emit('status_change', 'event play changed')

    def playlist_changed(self):
        logger.info('pl state changed')
        self.emit('status_change', 'event playlist changed')

    def options_changed(self):
        logger.info('op state changed')
        self.emit('status_change', 'event options changed')

    def volume_changed(self):
        logger.info('vol state changed')
        self.emit('status_change', 'event volume changed')
        
class WsContext(object):
    """
    This object is passed as the first argument to all Ws command handlers to
    give the command handlers access to important parts of Mopidy.
    """
    
    #: The current :class:`mopidy.frontends.ws.WsSession`.
    session = None

    #: The subsytems that we want to be notified about
    """
         - ``database``: the song database has been modified after update.
        - ``update``: a database update has started or finished. If the
          database was modified during the update, the database event is
          also emitted.
        - ``stored_playlist``: a stored playlist has been modified,
          renamed, created or deleted
        - ``playlist``: the current playlist has been modified
        - ``player``: the player has been started, stopped or seeked
        - ``mixer``: the volume has been changed
        - ``output``: an audio output has been enabled or disabled
        - ``options``: options like repeat, random, crossfade, replay gain
    """

    def __init__(self, session=None):
        logger.info('context strt')
        self.session = session
        #self.events = set()
#        self.events = ['mixer', 'options', 'player', 'playlist', 'stored_playlist', 'output', 'update', 'database']
        #self.subscriptions = set()
#        self.subscriptions = ['mixer', 'options', 'player', 'playlist', 'stored_playlist', 'output', 'update', 'database']
        self._backend = None
        self._mixer = None

    @property
    def backend(self):
        """
        The backend. An instance of :class:`mopidy.backends.base.Backend`.
        """
        if self._backend is None:
            backend_refs = registry.ActorRegistry.get_by_class(Backend)
            assert len(backend_refs) == 1, \
                'Expected exactly one running backend.'
            self._backend = backend_refs[0].proxy()
        return self._backend

    @property
    def mixer(self):
        """
        The mixer. An instance of :class:`mopidy.mixers.base.BaseMixer`.
        """
        if self._mixer is None:
            mixer_refs = registry.ActorRegistry.get_by_class(BaseMixer)
            assert len(mixer_refs) == 1, 'Expected exactly one running mixer.'
            self._mixer = mixer_refs[0].proxy()
        return self._mixer
     
