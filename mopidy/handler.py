import logging
import re
import sys

from mopidy import settings
from mopidy.backends.spotify import SpotifyBackend

logger = logging.getLogger('handler')

global _request_handlers
_request_handlers = {}

def register(pattern):
    def decorator(func):
        global _request_handlers
        if pattern in _request_handlers:
            raise ValueError(u'Tried to redefine handler for %s with %s' % (
                pattern, func))
        _request_handlers[pattern] = func
        return func
    return decorator

class MpdHandler(object):
    def __init__(self, session=None, backend=SpotifyBackend):
        self.session = session
        self.register_backend(backend())

    def handle_request(self, request):
        for pattern in _request_handlers:
            matches = re.match(pattern, request)
            if matches is not None:
                groups = matches.groupdict()
                return _request_handlers[pattern](self, **groups)
        logger.warning(u'Unhandled request: %s', request)
        return False

    def register_backend(self, backend):
        self.backend = backend

    @register(r'^add "(?P<uri>[^"]*)"$')
    def _add(self, uri):
        pass # TODO

    @register(r'^addid "(?P<uri>[^"]*)"( (?P<songpos>\d+))*$')
    def _add(self, uri, songpos=None):
        # TODO
        return {'id': 0}

    @register(r'^clear$')
    def _clear(self):
        pass # TODO

    @register(r'^clearerror$')
    def _clearerror(self):
        pass # TODO

    @register(r'^close$')
    def _close(self):
        self.session.do_close()

    @register(r'^consume "(?P<state>[01])"$')
    def _consume(self, state):
        state = int(state)
        if state:
            pass # TODO
        else:
            pass # TODO

    @register(r'^crossfade "(?P<seconds>\d+)"$')
    def _crossfade(self, seconds):
        seconds = int(seconds)
        pass # TODO

    @register(r'^currentsong$')
    def _currentsong(self):
        return self.backend.current_song()

    @register(r'^delete ((?P<songpos>\d+)|(?P<start>\d+):(?P<end>\d+)*)$')
    def _delete(self, songpos=None, start=None, end=None):
        pass # TODO

    @register(r'^deleteid (?P<songid>.*)$')
    def _deleteid(self, songid):
        pass # TODO

    @register(r'^$')
    def _empty(self):
        pass

    @register(r'^idle( (?P<subsystems>.+))*$')
    def _idle(self, subsystems=None):
        pass # TODO

    @register(r'^kill$')
    def _kill(self):
        self.session.do_kill()

    @register(r'^listplaylist (?P<name>.+)$')
    def _listplaylist(self, name):
        pass # TODO

    @register(r'^listplaylistinfo (?P<name>.+)$')
    def _listplaylistinfo(self, name):
        pass # TODO

    @register(r'^listplaylists$')
    def _listplaylists(self):
        return self.backend.playlists_list()

    @register(r'^load "(?P<name>.+)"$')
    def _load(self, name):
        return self.backend.playlist_load(name)

    @register(r'^lsinfo( "(?P<uri>[^"]*)")*$')
    def _lsinfo(self, uri):
        if uri == u'/':
            return self._listplaylists()
        # TODO
        return self._listplaylists()

    @register(r'^move ((?P<songpos>\d+)|(?P<start>\d+):(?P<end>\d+)*) (?P<to>\d+)$')
    def _move(self, songpos=None, start=None, end=None, to=None):
        pass # TODO

    @register(r'^moveid (?P<songid>\S+) (?P<to>\d+)$')
    def _moveid(self, songid, to):
        pass # TODO

    @register(r'^next$')
    def _next(self):
        pass # TODO

    @register(r'^password "(?P<password>[^"]+)"$')
    def _password(self, password):
        pass # TODO

    @register(r'^pause (?P<state>[01])$')
    def _pause(self, state):
        pass # TODO

    @register(r'^ping$')
    def _ping(self):
        pass

    @register(r'^play "(?P<songpos>\d+)"$')
    def _play(self, songpos):
        pass # TODO

    @register(r'^playid "(?P<songid>\d+)"$')
    def _playid(self, songid):
        return self.backend.play_id(int(songid))

    @register(r'^playlist$')
    def _playlist(self):
        return self._playlistinfo()

    @register(r'^playlistadd (?P<name>\S+) "(?P<uri>[^"]+)"$')
    def _playlistadd(self, name, uri):
        pass # TODO

    @register(r'^playlistclear (?P<name>\S+)$')
    def _playlistclear(self, name):
        pass # TODO

    @register(r'^playlistdelete (?P<name>\S+) (?P<songpos>\d+)$')
    def _playlistdelete(self, name, songpos):
        pass # TODO

    @register(r'^playlistfind (?P<tag>\S+) (?P<needle>\S+)$')
    def _playlistfind(self, tag, needle):
        pass # TODO

    @register(r'^playlistid( (?P<songid>\S+))*$')
    def _playlistid(self, songid=None):
        pass # TODO

    @register(r'^playlistinfo( "((?P<songpos>\d+)|(?P<start>\d+):(?P<end>\d+)*)")*$')
    def _playlistinfo(self, songpos=None, start=None, end=None):
        return self.backend.playlist_info(songpos, start, end)

    @register(r'^playlistmove (?P<name>\S+) (?P<songid>\S+) (?P<songpos>\d+)$')
    def _playlistdelete(self, name, songid, songpos):
        pass # TODO

    @register(r'^playlistsearch (?P<tag>\S+) (?P<needle>\S+)$')
    def _playlistsearch(self, tag, needle):
        pass # TODO

    @register(r'^plchanges "(?P<version>\d+)"$')
    def _plchanges(self, version):
        return self.backend.playlist_changes(version)

    @register(r'^plchangesposid (?P<version>\d+)$')
    def _plchangesposid(self, version):
        pass # TODO

    @register(r'^previous$')
    def _previous(self):
        pass # TODO

    @register(r'^rename (?P<old_name>\S+) (?P<new_name>\S+)$')
    def _rename(self, old_name, new_name):
        pass # TODO

    @register(r'^random "(?P<state>[01])"$')
    def _random(self, state):
        state = int(state)
        if state:
            pass # TODO
        else:
            pass # TODO

    @register(r'^repeat "(?P<state>[01])"$')
    def _repeat(self, state):
        state = int(state)
        if state:
            pass # TODO
        else:
            pass # TODO

    @register(r'^replay_gain_mode (?P<mode>(off|track|album))$')
    def _replay_gain_mode(self, mode):
        pass # TODO

    @register(r'^replay_gain_status$')
    def _replay_gain_status(self):
        return u'off' # TODO

    @register(r'^rm (?P<name>\S+)$')
    def _rm(self, name):
        pass # TODO

    @register(r'^save (?P<name>\S+)$')
    def _save(self, name):
        pass # TODO

    @register(r'^seek (?P<songpos>.+) (?P<seconds>\d+)$')
    def _seek(self, songpos, seconds):
        pass # TODO

    @register(r'^seekid (?P<songid>.+) (?P<seconds>\d+)$')
    def _seekid(self, songid, seconds):
        pass # TODO

    @register(r'^setvol "(?P<volume>-*\d+)"$')
    def _setvol(self, volume):
        volume = int(volume)
        if volume < 0:
            volume = 0
        if volume > 100:
            volume = 100
        pass # TODO

    @register(r'^shuffle( (?P<start>\d+):(?P<end>\d+)*)*$')
    def _shuffle(self, start=None, end=None):
        pass # TODO

    @register(r'^single "(?P<state>[01])"$')
    def _single(self, state):
        state = int(state)
        if state:
            pass # TODO
        else:
            pass # TODO

    @register(r'^stats$')
    def _stats(self):
        # TODO
        return {
            'artists': 0,
            'albums': 0,
            'songs': 0,
            'uptime': 0,
            'db_playtime': 0,
            'db_update': 0,
            'playtime': 0,
        }

    @register(r'^stop$')
    def _stop(self):
        self.backend.stop()

    @register(r'^status$')
    def _status(self):
        return {
            'volume': self.backend.status_volume(),
            'repeat': self.backend.status_repeat(),
            'random': self.backend.status_random(),
            'single': self.backend.status_single(),
            'consume': self.backend.status_consume(),
            'playlist': self.backend.status_playlist(),
            'playlistlength': self.backend.status_playlist_length(),
            'xfade': self.backend.status_xfade(),
            'state': self.backend.status_state(),
        }

    @register(r'^swap (?P<songpos1>\d+) (?P<songpos2>\d+)$')
    def _swap(self, songpos1, songpos2):
        pass # TODO

    @register(r'^swapid (?P<songid1>\S+) (?P<songid2>\S+)$')
    def _swapid(self, songid1, songid2):
        pass # TODO
