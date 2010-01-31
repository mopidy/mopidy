import logging
import re
import sys

from mopidy import settings
from mopidy.exceptions import MpdAckError, MpdNotImplemented

logger = logging.getLogger('mpd.handler')

_request_handlers = {}

def register(pattern):
    def decorator(func):
        if pattern in _request_handlers:
            raise ValueError(u'Tried to redefine handler for %s with %s' % (
                pattern, func))
        _request_handlers[pattern] = func
        return func
    return decorator

def flatten(the_list):
    result = []
    for element in the_list:
        if isinstance(element, list):
            result.extend(flatten(element))
        else:
            result.append(element)
    return result

class MpdHandler(object):
    def __init__(self, session=None, backend=None):
        self.session = session
        self.backend = backend
        self.command_list = False

    def handle_request(self, request, add_ok=True):
        if self.command_list is not False and request != u'command_list_end':
            self.command_list.append(request)
            return None
        for pattern in _request_handlers:
            matches = re.match(pattern, request)
            if matches is not None:
                groups = matches.groupdict()
                try:
                    result = _request_handlers[pattern](self, **groups)
                except MpdAckError, e:
                    return self.handle_response(u'ACK %s' % e, add_ok=False)
                if self.command_list is not False:
                    return None
                else:
                    return self.handle_response(result, add_ok)
        raise MpdAckError(u'Unknown command: %s' % request)

    def handle_response(self, result, add_ok=True):
        response = []
        if result is None:
            result = []
        elif not isinstance(result, list):
            result = [result]
        for line in flatten(result):
            if isinstance(line, dict):
                for (key, value) in line.items():
                    response.append(u'%s: %s' % (key, value))
            elif isinstance(line, tuple):
                (key, value) = line
                response.append(u'%s: %s' % (key, value))
            else:
                response.append(line)
        if add_ok:
            response.append(u'OK')
        return response

    @register(r'^add "(?P<uri>[^"]*)"$')
    def _add(self, uri):
        raise MpdNotImplemented # TODO

    @register(r'^addid "(?P<uri>[^"]*)"( (?P<songpos>\d+))*$')
    def _add(self, uri, songpos=None):
        raise MpdNotImplemented # TODO

    @register(r'^clear$')
    def _clear(self):
        raise MpdNotImplemented # TODO

    @register(r'^clearerror$')
    def _clearerror(self):
        raise MpdNotImplemented # TODO

    @register(r'^close$')
    def _close(self):
        self.session.do_close()

    @register(r'^command_list_begin$')
    def _command_list_begin(self):
        self.command_list = []
        self.command_list_ok = False

    @register(r'^command_list_ok_begin$')
    def _command_list_ok_begin(self):
        self.command_list = []
        self.command_list_ok = True

    @register(r'^command_list_end$')
    def _command_list_end(self):
        (command_list, self.command_list) = (self.command_list, False)
        (command_list_ok, self.command_list_ok) = (self.command_list_ok, False)
        result = []
        for command in command_list:
            response = self.handle_request(command, add_ok=False)
            if response is not None:
                result.append(response)
            if command_list_ok:
                response.append(u'list_OK')
        return result

    @register(r'^consume "(?P<state>[01])"$')
    def _consume(self, state):
        state = int(state)
        if state:
            raise MpdNotImplemented # TODO
        else:
            raise MpdNotImplemented # TODO

    @register(r'^count "(?P<tag>[^"]+)" "(?P<needle>[^"]+)"$')
    def _count(self, tag, needle):
        raise MpdNotImplemented # TODO

    @register(r'^crossfade "(?P<seconds>\d+)"$')
    def _crossfade(self, seconds):
        seconds = int(seconds)
        raise MpdNotImplemented # TODO

    @register(r'^currentsong$')
    def _currentsong(self):
        return self.backend.current_song()

    @register(r'^delete "(?P<songpos>\d+)"$')
    @register(r'^delete "(?P<start>\d+):(?P<end>\d+)*"$')
    def _delete(self, songpos=None, start=None, end=None):
        raise MpdNotImplemented # TODO

    @register(r'^deleteid "(?P<songid>\d+)"$')
    def _deleteid(self, songid):
        raise MpdNotImplemented # TODO

    @register(r'^$')
    def _empty(self):
        pass

    @register(r'^find "(?P<type>(album|artist|title))" "(?P<what>[^"]+)"$')
    def _find(self, type, what):
        raise MpdNotImplemented # TODO

    @register(r'^findadd "(?P<type>(album|artist|title))" "(?P<what>[^"]+)"$')
    def _findadd(self, type, what):
        result = self._find(type, what)
        # TODO Add result to current playlist
        #return result

    @register(r'^idle$')
    @register(r'^idle (?P<subsystems>.+)$')
    def _idle(self, subsystems=None):
        raise MpdNotImplemented # TODO

    @register(r'^kill$')
    def _kill(self):
        self.session.do_kill()

    @register(r'^list "(?P<type>artist)"$')
    @register(r'^list "(?P<type>album)"( "(?P<artist>[^"]+)")*$')
    def _list(self, type, artist=None):
        raise MpdNotImplemented # TODO

    @register(r'^listall "(?P<uri>[^"]+)"')
    def _listall(self, uri):
        raise MpdNotImplemented # TODO

    @register(r'^listallinfo "(?P<uri>[^"]+)"')
    def _listallinfo(self, uri):
        raise MpdNotImplemented # TODO

    @register(r'^listplaylist "(?P<name>[^"]+)"$')
    def _listplaylist(self, name):
        raise MpdNotImplemented # TODO

    @register(r'^listplaylistinfo "(?P<name>[^"]+)"$')
    def _listplaylistinfo(self, name):
        raise MpdNotImplemented # TODO

    @register(r'^listplaylists$')
    def _listplaylists(self):
        return self.backend.playlists_list()

    @register(r'^load "(?P<name>[^"]+)"$')
    def _load(self, name):
        return self.backend.playlist_load(name)

    @register(r'^lsinfo( "(?P<uri>[^"]*)")*$')
    def _lsinfo(self, uri):
        if uri == u'/' or uri is None:
            return self._listplaylists()
        raise MpdNotImplemented # TODO

    @register(r'^move "(?P<songpos>\d+)" "(?P<to>\d+)"$')
    @register(r'^move "(?P<start>\d+):(?P<end>\d+)*" "(?P<to>\d+)"$')
    def _move(self, songpos=None, start=None, end=None, to=None):
        raise MpdNotImplemented # TODO

    @register(r'^moveid "(?P<songid>\d+)" "(?P<to>\d+)"$')
    def _moveid(self, songid, to):
        raise MpdNotImplemented # TODO

    @register(r'^next$')
    def _next(self):
        return self.backend.next()

    @register(r'^password "(?P<password>[^"]+)"$')
    def _password(self, password):
        raise MpdNotImplemented # TODO

    @register(r'^pause "(?P<state>[01])"$')
    def _pause(self, state):
        if int(state):
            self.backend.pause()
        else:
            self.backend.resume()

    @register(r'^ping$')
    def _ping(self):
        pass

    @register(r'^play$')
    def _play(self):
        return self.backend.play()

    @register(r'^play "(?P<songpos>\d+)"$')
    def _playpos(self, songpos):
        return self.backend.play(songpos=int(songpos))

    @register(r'^playid "(?P<songid>\d+)"$')
    def _playid(self, songid):
        return self.backend.play(songid=int(songid))

    @register(r'^playlist$')
    def _playlist(self):
        return self._playlistinfo()

    @register(r'^playlistadd "(?P<name>[^"]+)" "(?P<uri>[^"]+)"$')
    def _playlistadd(self, name, uri):
        raise MpdNotImplemented # TODO

    @register(r'^playlistclear "(?P<name>[^"]+)"$')
    def _playlistclear(self, name):
        raise MpdNotImplemented # TODO

    @register(r'^playlistdelete "(?P<name>[^"]+)" "(?P<songpos>\d+)"$')
    def _playlistdelete(self, name, songpos):
        raise MpdNotImplemented # TODO

    @register(r'^playlistfind "(?P<tag>[^"]+)" "(?P<needle>[^"]+)"$')
    def _playlistfind(self, tag, needle):
        raise MpdNotImplemented # TODO

    @register(r'^playlistid( "(?P<songid>\S+)")*$')
    def _playlistid(self, songid=None):
        return self.backend.playlist_info(songid, None, None)

    @register(r'^playlistinfo$')
    @register(r'^playlistinfo "(?P<songpos>\d+)"$')
    @register(r'^playlistinfo "(?P<start>\d+):(?P<end>\d+)*"$')
    def _playlistinfo(self, songpos=None, start=None, end=None):
        return self.backend.playlist_info(songpos, start, end)

    @register(r'^playlistmove "(?P<name>[^"]+)" "(?P<songid>\d+)" "(?P<songpos>\d+)"$')
    def _playlistdelete(self, name, songid, songpos):
        raise MpdNotImplemented # TODO

    @register(r'^playlistsearch "(?P<tag>[^"]+)" "(?P<needle>[^"]+)"$')
    def _playlistsearch(self, tag, needle):
        raise MpdNotImplemented # TODO

    @register(r'^plchanges "(?P<version>\d+)"$')
    def _plchanges(self, version):
        return self.backend.playlist_changes_since(version)

    @register(r'^plchangesposid "(?P<version>\d+)"$')
    def _plchangesposid(self, version):
        raise MpdNotImplemented # TODO

    @register(r'^previous$')
    def _previous(self):
        return self.backend.previous()

    @register(r'^rename "(?P<old_name>[^"]+)" "(?P<new_name>[^"]+)"$')
    def _rename(self, old_name, new_name):
        raise MpdNotImplemented # TODO

    @register(r'^random "(?P<state>[01])"$')
    def _random(self, state):
        state = int(state)
        if state:
            raise MpdNotImplemented # TODO
        else:
            raise MpdNotImplemented # TODO

    @register(r'^repeat "(?P<state>[01])"$')
    def _repeat(self, state):
        state = int(state)
        if state:
            raise MpdNotImplemented # TODO
        else:
            raise MpdNotImplemented # TODO

    @register(r'^replay_gain_mode "(?P<mode>(off|track|album))"$')
    def _replay_gain_mode(self, mode):
        raise MpdNotImplemented # TODO

    @register(r'^replay_gain_status$')
    def _replay_gain_status(self):
        return u'off' # TODO

    @register(r'^rescan( "(?P<uri>[^"]+)")*$')
    def _update(self, uri=None):
        return self._update(uri, rescan_unmodified_files=True)

    @register(r'^rm "(?P<name>[^"]+)"$')
    def _rm(self, name):
        raise MpdNotImplemented # TODO

    @register(r'^save "(?P<name>[^"]+)"$')
    def _save(self, name):
        raise MpdNotImplemented # TODO

    @register(r'^search "(?P<type>(album|artist|filename|title))" "(?P<what>[^"]+)"$')
    def _search(self, type, what):
        return self.backend.search(type, what)

    @register(r'^seek "(?P<songpos>\d+)" "(?P<seconds>\d+)"$')
    def _seek(self, songpos, seconds):
        raise MpdNotImplemented # TODO

    @register(r'^seekid "(?P<songid>\d+)" "(?P<seconds>\d+)"$')
    def _seekid(self, songid, seconds):
        raise MpdNotImplemented # TODO

    @register(r'^setvol "(?P<volume>-*\d+)"$')
    def _setvol(self, volume):
        volume = int(volume)
        if volume < 0:
            volume = 0
        if volume > 100:
            volume = 100
        raise MpdNotImplemented # TODO

    @register(r'^shuffle$')
    @register(r'^shuffle "(?P<start>\d+):(?P<end>\d+)*"$')
    def _shuffle(self, start=None, end=None):
        raise MpdNotImplemented # TODO

    @register(r'^single "(?P<state>[01])"$')
    def _single(self, state):
        state = int(state)
        if state:
            raise MpdNotImplemented # TODO
        else:
            raise MpdNotImplemented # TODO

    @register(r'^stats$')
    def _stats(self):
        pass # TODO
        return {
            'artists': 0,
            'albums': 0,
            'songs': 0,
            'uptime': self.session.stats_uptime(),
            'db_playtime': 0,
            'db_update': 0,
            'playtime': 0,
        }

    @register(r'^stop$')
    def _stop(self):
        self.backend.stop()

    @register(r'^status$')
    def _status(self):
        result = [
            ('volume', self.backend.status_volume()),
            ('repeat', self.backend.status_repeat()),
            ('random', self.backend.status_random()),
            ('single', self.backend.status_single()),
            ('consume', self.backend.status_consume()),
            ('playlist', self.backend.status_playlist()),
            ('playlistlength', self.backend.status_playlist_length()),
            ('xfade', self.backend.status_xfade()),
            ('state', self.backend.status_state()),
        ]
        if self.backend.status_playlist_length() > 0:
            result.append(('song', self.backend.status_song_id()))
            result.append(('songid', self.backend.status_song_id()))
        if self.backend.state in (self.backend.PLAY, self.backend.PAUSE):
            result.append(('time', self.backend.status_time()))
            result.append(('bitrate', self.backend.status_bitrate()))
        return result

    @register(r'^swap "(?P<songpos1>\d+)" "(?P<songpos2>\d+)"$')
    def _swap(self, songpos1, songpos2):
        raise MpdNotImplemented # TODO

    @register(r'^swapid "(?P<songid1>\d+)" "(?P<songid2>\d+)"$')
    def _swapid(self, songid1, songid2):
        raise MpdNotImplemented # TODO

    @register(r'^update( "(?P<uri>[^"]+)")*$')
    def _update(self, uri=None, rescan_unmodified_files=False):
        return {'updating_db': 0} # TODO

    @register(r'^urlhandlers$')
    def _urlhandlers(self):
        return self.backend.url_handlers()
