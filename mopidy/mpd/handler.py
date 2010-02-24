"""
Our MPD protocol implementation

This is partly based upon the `MPD protocol documentation
<http://www.musicpd.org/doc/protocol/>`_, which is a useful resource, but it is
rather incomplete with regards to data formats, both for requests and
responses. Thus, we have had to talk a great deal with the the original `MPD
server <http://mpd.wikia.com/>`_ using telnet to get the details we need to
implement our own MPD server which is compatible with the numerous existing
`MPD clients <http://mpd.wikia.com/wiki/Clients>`_.
"""

import logging
import re
import sys

from mopidy.exceptions import MpdAckError, MpdNotImplemented

logger = logging.getLogger('mpd.handler')

_request_handlers = {}

def handle_pattern(pattern):
    def decorator(func):
        if pattern in _request_handlers:
            raise ValueError(u'Tried to redefine handler for %s with %s' % (
                pattern, func))
        _request_handlers[pattern] = func
        func.__doc__ = '        - **Pattern:** ``%s``\n\n%s' % (
            pattern, func.__doc__ or '')
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
        if add_ok and (not response or not response[-1].startswith(u'ACK')):
            response.append(u'OK')
        return response

    @handle_pattern(r'^ack$')
    def _ack(self):
        """
        Always returns an 'ACK'. Not a part of the MPD protocol.
        """
        raise MpdNotImplemented

    @handle_pattern(r'^add "(?P<uri>[^"]*)"$')
    def _add(self, uri):
        """
        *musicpd.org, current playlist section:*

            ``add {URI}``

            Adds the file ``URI`` to the playlist (directories add recursively).
            ``URI`` can also be a single file.
        """
        raise MpdNotImplemented # TODO

    @handle_pattern(r'^addid "(?P<uri>[^"]*)"( (?P<songpos>\d+))*$')
    def _addid(self, uri, songpos=None):
        """
        *musicpd.org, current playlist section:*

            ``addid {URI} [POSITION]``

            Adds a song to the playlist (non-recursive) and returns the song id.

            ``URI`` is always a single file or URL. For example::

                addid "foo.mp3"
                Id: 999
                OK
        """
        raise MpdNotImplemented # TODO

    @handle_pattern(r'^clear$')
    def _clear(self):
        """
        *musicpd.org, current playlist section:*

            ``clear``

            Clears the current playlist.
        """
        raise MpdNotImplemented # TODO

    @handle_pattern(r'^clearerror$')
    def _clearerror(self):
        """
        *musicpd.org, status section:*

            ``clearerror``

            Clears the current error message in status (this is also
            accomplished by any command that starts playback).
        """
        raise MpdNotImplemented # TODO

    @handle_pattern(r'^close$')
    def _close(self):
        """
        *musicpd.org, connection section:*

            ``close``

            Closes the connection to MPD.
        """
        self.session.do_close()

    @handle_pattern(r'^command_list_begin$')
    def _command_list_begin(self):
        """
        *musicpd.org, command list section:*

            To facilitate faster adding of files etc. you can pass a list of
            commands all at once using a command list. The command list begins
            with ``command_list_begin`` or ``command_list_ok_begin`` and ends
            with ``command_list_end``.

            It does not execute any commands until the list has ended. The
            return value is whatever the return for a list of commands is. On
            success for all commands, ``OK`` is returned. If a command fails,
            no more commands are executed and the appropriate ``ACK`` error is
            returned. If ``command_list_ok_begin`` is used, ``list_OK`` is
            returned for each successful command executed in the command list.
        """
        self.command_list = []
        self.command_list_ok = False

    @handle_pattern(r'^command_list_ok_begin$')
    def _command_list_ok_begin(self):
        """See :meth:`_command_list_begin`."""
        self.command_list = []
        self.command_list_ok = True

    @handle_pattern(r'^command_list_end$')
    def _command_list_end(self):
        """See :meth:`_command_list_begin`."""
        (command_list, self.command_list) = (self.command_list, False)
        (command_list_ok, self.command_list_ok) = (self.command_list_ok, False)
        result = []
        for command in command_list:
            response = self.handle_request(command, add_ok=False)
            if response is not None:
                result.append(response)
            if response and response[-1].startswith(u'ACK'):
                return result
            if command_list_ok:
                response.append(u'list_OK')
        return result

    @handle_pattern(r'^commands$')
    def _commands(self):
        """
        *musicpd.org, reflection section:*

            ``commands``

            Shows which commands the current user has access to.
        """
        raise MpdNotImplemented # TODO

    @handle_pattern(r'^consume "(?P<state>[01])"$')
    def _consume(self, state):
        """
        *musicpd.org, playback section:*

            ``consume {STATE}``

            Sets consume state to ``STATE``, ``STATE`` should be 0 or
            1. When consume is activated, each song played is removed from
            playlist.
        """
        state = int(state)
        if state:
            raise MpdNotImplemented # TODO
        else:
            raise MpdNotImplemented # TODO

    @handle_pattern(r'^count "(?P<tag>[^"]+)" "(?P<needle>[^"]+)"$')
    def _count(self, tag, needle):
        """
        *musicpd.org, music database section:*

            ``count {TAG} {NEEDLE}``

            Counts the number of songs and their total playtime in the db
            matching ``TAG`` exactly.
        """
        raise MpdNotImplemented # TODO

    @handle_pattern(r'^crossfade "(?P<seconds>\d+)"$')
    def _crossfade(self, seconds):
        """
        *musicpd.org, playback section:*

            ``crossfade {SECONDS}``

            Sets crossfading between songs.
        """
        seconds = int(seconds)
        raise MpdNotImplemented # TODO

    @handle_pattern(r'^currentsong$')
    def _currentsong(self):
        """
        *musicpd.org, status section:*

            ``currentsong``

            Displays the song info of the current song (same song that is
            identified in status).
        """
        if self.backend.playback.current_track is not None:
            return self.backend.playback.current_track.mpd_format(
                position=self.backend.playback.playlist_position)

    @handle_pattern(r'^decoders$')
    def _decoders(self):
        """
        *musicpd.org, reflection section:*

            ``decoders``

            Print a list of decoder plugins, followed by their supported
            suffixes and MIME types. Example response::

                plugin: mad
                suffix: mp3
                suffix: mp2
                mime_type: audio/mpeg
                plugin: mpcdec
                suffix: mpc
        """
        raise MpdNotImplemented # TODO

    @handle_pattern(r'^delete "(?P<songpos>\d+)"$')
    @handle_pattern(r'^delete "(?P<start>\d+):(?P<end>\d+)*"$')
    def _delete(self, songpos=None, start=None, end=None):
        """
        *musicpd.org, current playlist section:*

            ``delete [{POS} | {START:END}]``

            Deletes a song from the playlist.
        """
        raise MpdNotImplemented # TODO

    @handle_pattern(r'^deleteid "(?P<songid>\d+)"$')
    def _deleteid(self, songid):
        """
        *musicpd.org, current playlist section:*

            ``deleteid {SONGID}``

            Deletes the song ``SONGID`` from the playlist
        """
        songid = int(songid)
        try:
            track = self.backend.current_playlist.get_by_id(songid)
            return self.backend.current_playlist.remove(track)
        except KeyError, e:
            raise MpdAckError(unicode(e))

    @handle_pattern(r'^disableoutput "(?P<outputid>\d+)"$')
    def _disableoutput(self, outputid):
        """
        *musicpd.org, audio output section:*

            ``disableoutput``

            Turns an output off.
        """
        raise MpdNotImplemented # TODO

    @handle_pattern(r'^$')
    def _empty(self):
        """The original MPD server returns ``OK`` on an empty request.``"""
        pass

    @handle_pattern(r'^enableoutput "(?P<outputid>\d+)"$')
    def _enableoutput(self, outputid):
        """
        *musicpd.org, audio output section:*

            ``enableoutput``

            Turns an output on.
        """
        raise MpdNotImplemented # TODO

    @handle_pattern(r'^find "(?P<type>(album|artist|title))" "(?P<what>[^"]+)"$')
    def _find(self, type, what):
        """
        *musicpd.org, music database section:*

            ``find {TYPE} {WHAT}``

            Finds songs in the db that are exactly ``WHAT``. ``TYPE`` should be
            ``album``, ``artist``, or ``title``. ``WHAT`` is what to find.
        """
        if type == u'title':
            type = u'track'
        return self.backend.library.find_exact(type, what).mpd_format(
            search_result=True)

    @handle_pattern(r'^findadd "(?P<type>(album|artist|title))" "(?P<what>[^"]+)"$')
    def _findadd(self, type, what):
        """
        *musicpd.org, music database section:*

            ``findadd {TYPE} {WHAT}``

            Finds songs in the db that are exactly ``WHAT`` and adds them to
            current playlist. ``TYPE`` can be any tag supported by MPD.
            ``WHAT`` is what to find.
        """
        result = self._find(type, what)
        # TODO Add result to current playlist
        #return result

    @handle_pattern(r'^idle$')
    @handle_pattern(r'^idle (?P<subsystems>.+)$')
    def _idle(self, subsystems=None):
        """
        *musicpd.org, status section:*

            ``idle [SUBSYSTEMS...]``

            Waits until there is a noteworthy change in one or more of MPD's
            subsystems. As soon as there is one, it lists all changed systems
            in a line in the format ``changed: SUBSYSTEM``, where ``SUBSYSTEM``
            is one of the following:

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

            While a client is waiting for idle results, the server disables
            timeouts, allowing a client to wait for events as long as MPD runs.
            The idle command can be canceled by sending the command ``noidle``
            (no other commands are allowed). MPD will then leave idle mode and
            print results immediately; might be empty at this time.

            If the optional ``SUBSYSTEMS`` argument is used, MPD will only send
            notifications when something changed in one of the specified
            subsystems.
        """
        raise MpdNotImplemented # TODO

    @handle_pattern(r'^kill$')
    def _kill(self):
        """
        *musicpd.org, connection section:*

            ``kill``

            Kills MPD.
        """
        self.session.do_kill()

    @handle_pattern(r'^list "(?P<type>artist)"$')
    @handle_pattern(r'^list "(?P<type>album)"( "(?P<artist>[^"]+)")*$')
    def _list(self, type, artist=None):
        """
        *musicpd.org, music database section:*

            ``list {TYPE} [ARTIST]``

            Lists all tags of the specified type. ``TYPE`` should be ``album``
            or artist.

            ``ARTIST`` is an optional parameter when type is ``album``, this
            specifies to list albums by an artist.
        """
        raise MpdNotImplemented # TODO

    @handle_pattern(r'^listall "(?P<uri>[^"]+)"')
    def _listall(self, uri):
        """
        *musicpd.org, music database section:*

            ``listall [URI]``

            Lists all songs and directories in ``URI``.
        """
        raise MpdNotImplemented # TODO

    @handle_pattern(r'^listallinfo "(?P<uri>[^"]+)"')
    def _listallinfo(self, uri):
        """
        *musicpd.org, music database section:*

            ``listallinfo [URI]``

            Same as ``listall``, except it also returns metadata info in the
            same format as ``lsinfo``.
        """
        raise MpdNotImplemented # TODO

    @handle_pattern(r'^listplaylist "(?P<name>[^"]+)"$')
    def _listplaylist(self, name):
        """
        *musicpd.org, stored playlists section:*

            ``listplaylist {NAME}``

            Lists the files in the playlist ``NAME.m3u``.

        Output format::

            file: relative/path/to/file1.flac
            file: relative/path/to/file2.ogg
            file: relative/path/to/file3.mp3
        """
        try:
            return ['file: %s' % t.uri
                for t in self.backend.stored_playlists.get_by_name(name).tracks]
        except KeyError, e:
            raise MpdAckError(e)

    @handle_pattern(r'^listplaylistinfo "(?P<name>[^"]+)"$')
    def _listplaylistinfo(self, name):
        """
        *musicpd.org, stored playlists section:*

            ``listplaylistinfo {NAME}``

            Lists songs in the playlist ``NAME.m3u``.

        Output format:

            Standard track listing, with fields: file, Time, Title, Date,
            Album, Artist, Track
        """
        try:
            return self.backend.stored_playlists.get_by_name(name).mpd_format(
                search_result=True)
        except KeyError, e:
            raise MpdAckError(e)

    @handle_pattern(r'^listplaylists$')
    def _listplaylists(self):
        """
        *musicpd.org, stored playlists section:*

            ``listplaylists``

            Prints a list of the playlist directory.

            After each playlist name the server sends its last modification
            time as attribute ``Last-Modified`` in ISO 8601 format. To avoid
            problems due to clock differences between clients and the server,
            clients should not compare this value with their local clock.

        Output format::

            playlist: a
            Last-Modified: 2010-02-06T02:10:25Z
            playlist: b
            Last-Modified: 2010-02-06T02:11:08Z
        """
        # TODO Add Last-Modified attribute to output
        return [u'playlist: %s' % p.name
            for p in self.backend.stored_playlists.playlists]

    @handle_pattern(r'^load "(?P<name>[^"]+)"$')
    def _load(self, name):
        """
        *musicpd.org, stored playlists section:*

            ``load {NAME}``

            Loads the playlist ``NAME.m3u`` from the playlist directory.
        """
        matches = self.backend.stored_playlists.search(name)
        if matches:
            self.backend.current_playlist.load(matches[0])
            self.backend.playback.new_playlist_loaded_callback()

    @handle_pattern(r'^lsinfo$')
    @handle_pattern(r'^lsinfo "(?P<uri>[^"]*)"$')
    def _lsinfo(self, uri=None):
        """
        *musicpd.org, music database section:*

            ``lsinfo [URI]``

            Lists the contents of the directory ``URI``.

            When listing the root directory, this currently returns the list of
            stored playlists. This behavior is deprecated; use
            ``listplaylists`` instead.
        """
        if uri == u'/' or uri is None:
            return self._listplaylists()
        raise MpdNotImplemented # TODO

    @handle_pattern(r'^move "(?P<songpos>\d+)" "(?P<to>\d+)"$')
    @handle_pattern(r'^move "(?P<start>\d+):(?P<end>\d+)*" "(?P<to>\d+)"$')
    def _move(self, songpos=None, start=None, end=None, to=None):
        """
        *musicpd.org, current playlist section:*

            ``move [{FROM} | {START:END}] {TO}``

            Moves the song at ``FROM`` or range of songs at ``START:END`` to
            ``TO`` in the playlist.
        """
        raise MpdNotImplemented # TODO

    @handle_pattern(r'^moveid "(?P<songid>\d+)" "(?P<to>\d+)"$')
    def _moveid(self, songid, to):
        """
        *musicpd.org, current playlist section:*

            ``moveid {FROM} {TO}``

            Moves the song with ``FROM`` (songid) to ``TO` (playlist index) in
            the playlist. If ``TO`` is negative, it is relative to the current
            song in the playlist (if there is one).
        """
        raise MpdNotImplemented # TODO

    @handle_pattern(r'^next$')
    def _next(self):
        """
        *musicpd.org, playback section:*

            ``next``

            Plays next song in the playlist.
        """
        return self.backend.playback.next()

    @handle_pattern(r'^noidle$')
    def _noidle(self):
        """See :meth:`_idle`."""
        raise MpdNotImplemented # TODO

    @handle_pattern(r'^notcommands$')
    def _notcommands(self):
        """
        *musicpd.org, reflection section:*

            ``notcommands``

            Shows which commands the current user does not have access to.
        """
        raise MpdNotImplemented # TODO

    @handle_pattern(r'^outputs$')
    def _outputs(self):
        """
        *musicpd.org, audio output section:*

            ``outputs``

            Shows information about all outputs.
        """
        return [
            ('outputid', 0),
            ('outputname', self.backend.__class__.__name__),
            ('outputenabled', 1),
        ]

    @handle_pattern(r'^password "(?P<password>[^"]+)"$')
    def _password(self, password):
        """
        *musicpd.org, connection section:*

            ``password {PASSWORD}``

            This is used for authentication with the server. ``PASSWORD`` is
            simply the plaintext password.
        """
        raise MpdNotImplemented # TODO

    @handle_pattern(r'^pause "(?P<state>[01])"$')
    def _pause(self, state):
        """
        *musicpd.org, playback section:*

            ``pause {PAUSE}``

            Toggles pause/resumes playing, ``PAUSE`` is 0 or 1.
        """
        if int(state):
            self.backend.playback.pause()
        else:
            self.backend.playback.resume()

    @handle_pattern(r'^ping$')
    def _ping(self):
        """
        *musicpd.org, connection section:*

            ``ping``

            Does nothing but return ``OK``.
        """
        pass

    @handle_pattern(r'^play$')
    def _play(self):
        """
        The original MPD server resumes from the paused state on ``play``
        without arguments.
        """
        return self.backend.playback.play()

    @handle_pattern(r'^play "(?P<songpos>\d+)"$')
    def _playpos(self, songpos):
        """
        *musicpd.org, playback section:*

            ``play [SONGPOS]``

            Begins playing the playlist at song number ``SONGPOS``.
        """
        songpos = int(songpos)
        try:
            track = self.backend.current_playlist.playlist.tracks[songpos]
            return self.backend.playback.play(track)
        except IndexError:
            raise MpdAckError(u'Position out of bounds')

    @handle_pattern(r'^playid "(?P<songid>\d+)"$')
    def _playid(self, songid):
        """
        *musicpd.org, playback section:*

            ``playid [SONGID]``

            Begins playing the playlist at song ``SONGID``.
        """
        songid = int(songid)
        try:
            track = self.backend.current_playlist.get_by_id(songid)
            return self.backend.playback.play(track)
        except KeyError, e:
            raise MpdAckError(unicode(e))

    @handle_pattern(r'^playlist$')
    def _playlist(self):
        """
        *musicpd.org, current playlist section:*

            ``playlist``

            Displays the current playlist.

            .. note::

                Do not use this, instead use ``playlistinfo``.
        """
        return self._playlistinfo()

    @handle_pattern(r'^playlistadd "(?P<name>[^"]+)" "(?P<uri>[^"]+)"$')
    def _playlistadd(self, name, uri):
        """
        *musicpd.org, stored playlists section:*

            ``playlistadd {NAME} {URI}``

            Adds ``URI`` to the playlist ``NAME.m3u``.

            ``NAME.m3u`` will be created if it does not exist.
        """
        raise MpdNotImplemented # TODO

    @handle_pattern(r'^playlistclear "(?P<name>[^"]+)"$')
    def _playlistclear(self, name):
        """
        *musicpd.org, stored playlists section:*

            ``playlistclear {NAME}``

            Clears the playlist ``NAME.m3u``.
        """
        raise MpdNotImplemented # TODO

    @handle_pattern(r'^playlistdelete "(?P<name>[^"]+)" "(?P<songpos>\d+)"$')
    def _playlistdelete(self, name, songpos):
        """
        *musicpd.org, stored playlists section:*

            ``playlistdelete {NAME} {SONGPOS}``

            Deletes ``SONGPOS`` from the playlist ``NAME.m3u``.
        """
        raise MpdNotImplemented # TODO

    @handle_pattern(r'^playlistfind "(?P<tag>[^"]+)" "(?P<needle>[^"]+)"$')
    def _playlistfind(self, tag, needle):
        """
        *musicpd.org, current playlist section:*

            ``playlistfind {TAG} {NEEDLE}``

            Finds songs in the current playlist with strict matching.
        """
        raise MpdNotImplemented # TODO

    @handle_pattern(r'^playlistid( "(?P<songid>\S+)")*$')
    def _playlistid(self, songid=None):
        """
        *musicpd.org, current playlist section:*

            ``playlistid {SONGID}``

            Displays a list of songs in the playlist. ``SONGID`` is optional
            and specifies a single song to display info for.
        """
        # TODO Limit selection to songid
        return self.backend.current_playlist.playlist.mpd_format()

    @handle_pattern(r'^playlistinfo$')
    @handle_pattern(r'^playlistinfo "(?P<songpos>\d+)"$')
    @handle_pattern(r'^playlistinfo "(?P<start>\d+):(?P<end>\d+)*"$')
    def _playlistinfo(self, songpos=None, start=None, end=None):
        """
        *musicpd.org, current playlist section:*

            ``playlistinfo [[SONGPOS] | [START:END]]``

            Displays a list of all songs in the playlist, or if the optional
            argument is given, displays information only for the song
            ``SONGPOS`` or the range of songs ``START:END``.
        """
        if songpos is not None:
            songpos = int(songpos)
            return self.backend.current_playlist.playlist.mpd_format(
                songpos, songpos + 1)
        else:
            if start is None:
                start = 0
            start = int(start)
            if end is not None:
                end = int(end)
            return self.backend.current_playlist.playlist.mpd_format(start, end)

    @handle_pattern(r'^playlistmove "(?P<name>[^"]+)" "(?P<songid>\d+)" "(?P<songpos>\d+)"$')
    def _playlistmove(self, name, songid, songpos):
        """
        *musicpd.org, stored playlists section:*

            ``playlistmove {NAME} {SONGID} {SONGPOS}``

            Moves ``SONGID`` in the playlist ``NAME.m3u`` to the position
            ``SONGPOS``.
        """
        raise MpdNotImplemented # TODO

    @handle_pattern(r'^playlistsearch "(?P<tag>[^"]+)" "(?P<needle>[^"]+)"$')
    def _playlistsearch(self, tag, needle):
        """
        *musicpd.org, current playlist section:*

            ``playlistsearch {TAG} {NEEDLE}``

            Searches case-sensitively for partial matches in the current
            playlist.
        """
        raise MpdNotImplemented # TODO

    @handle_pattern(r'^plchanges "(?P<version>\d+)"$')
    def _plchanges(self, version):
        """
        *musicpd.org, current playlist section:*

            ``plchanges {VERSION}``

            Displays changed songs currently in the playlist since ``VERSION``.

            To detect songs that were deleted at the end of the playlist, use
            ``playlistlength`` returned by status command.
        """
        if int(version) < self.backend.current_playlist.version:
            return self.backend.current_playlist.playlist.mpd_format()

    @handle_pattern(r'^plchangesposid "(?P<version>\d+)"$')
    def _plchangesposid(self, version):
        """
        *musicpd.org, current playlist section:*

            ``plchangesposid {VERSION}``

            Displays changed songs currently in the playlist since ``VERSION``.
            This function only returns the position and the id of the changed
            song, not the complete metadata. This is more bandwidth efficient.

            To detect songs that were deleted at the end of the playlist, use
            ``playlistlength`` returned by status command.
        """
        raise MpdNotImplemented # TODO

    @handle_pattern(r'^previous$')
    def _previous(self):
        """
        *musicpd.org, playback section:*

            ``previous``

            Plays previous song in the playlist.
        """
        return self.backend.playback.previous()

    @handle_pattern(r'^rename "(?P<old_name>[^"]+)" "(?P<new_name>[^"]+)"$')
    def _rename(self, old_name, new_name):
        """
        *musicpd.org, stored playlists section:*

            ``rename {NAME} {NEW_NAME}``

            Renames the playlist ``NAME.m3u`` to ``NEW_NAME.m3u``.
        """
        raise MpdNotImplemented # TODO

    @handle_pattern(r'^random "(?P<state>[01])"$')
    def _random(self, state):
        """
        *musicpd.org, playback section:*

            ``random {STATE}``

            Sets random state to ``STATE``, ``STATE`` should be 0 or 1.
        """
        state = int(state)
        if state:
            raise MpdNotImplemented # TODO
        else:
            raise MpdNotImplemented # TODO

    @handle_pattern(r'^repeat "(?P<state>[01])"$')
    def _repeat(self, state):
        """
        *musicpd.org, playback section:*

            ``repeat {STATE}``

            Sets repeat state to ``STATE``, ``STATE`` should be 0 or 1.
        """
        state = int(state)
        if state:
            raise MpdNotImplemented # TODO
        else:
            raise MpdNotImplemented # TODO

    @handle_pattern(r'^replay_gain_mode "(?P<mode>(off|track|album))"$')
    def _replay_gain_mode(self, mode):
        """
        *musicpd.org, playback section:*

            ``replay_gain_mode {MODE}``

            Sets the replay gain mode. One of ``off``, ``track``, ``album``.

            Changing the mode during playback may take several seconds, because
            the new settings does not affect the buffered data.

            This command triggers the options idle event.
        """
        raise MpdNotImplemented # TODO

    @handle_pattern(r'^replay_gain_status$')
    def _replay_gain_status(self):
        """
        *musicpd.org, playback section:*

            ``replay_gain_status``

            Prints replay gain options. Currently, only the variable
            ``replay_gain_mode`` is returned.
        """
        return u'off' # TODO

    @handle_pattern(r'^rescan( "(?P<uri>[^"]+)")*$')
    def _rescan(self, uri=None):
        """
        *musicpd.org, music database section:*

            ``rescan [URI]``

            Same as ``update``, but also rescans unmodified files.
        """
        return self._update(uri, rescan_unmodified_files=True)

    @handle_pattern(r'^rm "(?P<name>[^"]+)"$')
    def _rm(self, name):
        """
        *musicpd.org, stored playlists section:*

            ``rm {NAME}``

            Removes the playlist ``NAME.m3u`` from the playlist directory.
        """
        raise MpdNotImplemented # TODO

    @handle_pattern(r'^save "(?P<name>[^"]+)"$')
    def _save(self, name):
        """
        *musicpd.org, stored playlists section:*

            ``save {NAME}``

            Saves the current playlist to ``NAME.m3u`` in the playlist
            directory.
        """
        raise MpdNotImplemented # TODO

    @handle_pattern(r'^search "(?P<type>(album|artist|filename|title))" "(?P<what>[^"]+)"$')
    def _search(self, type, what):
        """
        *musicpd.org, music database section:*

            ``search {TYPE} {WHAT}``

            Searches for any song that contains ``WHAT``. ``TYPE`` can be
            ``title``, ``artist``, ``album`` or ``filename``. Search is not
            case sensitive.
        """
        if type == u'title':
            type = u'track'
        return self.backend.library.search(type, what).mpd_format(
            search_result=True)

    @handle_pattern(r'^seek "(?P<songpos>\d+)" "(?P<seconds>\d+)"$')
    def _seek(self, songpos, seconds):
        """
        *musicpd.org, playback section:*

            ``seek {SONGPOS} {TIME}``

            Seeks to the position ``TIME`` (in seconds) of entry ``SONGPOS`` in
            the playlist.
        """
        raise MpdNotImplemented # TODO

    @handle_pattern(r'^seekid "(?P<songid>\d+)" "(?P<seconds>\d+)"$')
    def _seekid(self, songid, seconds):
        """
        *musicpd.org, playback section:*

            ``seekid {SONGID} {TIME}``

            Seeks to the position ``TIME`` (in seconds) of song ``SONGID``.
        """
        raise MpdNotImplemented # TODO

    @handle_pattern(r'^setvol "(?P<volume>[-+]*\d+)"$')
    def _setvol(self, volume):
        """
        *musicpd.org, playback section:*

            ``setvol {VOL}``

            Sets volume to ``VOL``, the range of volume is 0-100.
        """
        volume = int(volume)
        if volume < 0:
            volume = 0
        if volume > 100:
            volume = 100
        self.backend.playback.volume = volume

    @handle_pattern(r'^shuffle$')
    @handle_pattern(r'^shuffle "(?P<start>\d+):(?P<end>\d+)*"$')
    def _shuffle(self, start=None, end=None):
        """
        *musicpd.org, current playlist section:*

            ``shuffle [START:END]``

            Shuffles the current playlist. ``START:END`` is optional and
            specifies a range of songs.
        """
        raise MpdNotImplemented # TODO

    @handle_pattern(r'^single "(?P<state>[01])"$')
    def _single(self, state):
        """
        *musicpd.org, playback section:*

            ``single {STATE}``

            Sets single state to ``STATE``, ``STATE`` should be 0 or 1. When
            single is activated, playback is stopped after current song, or
            song is repeated if the ``repeat`` mode is enabled.
        """
        state = int(state)
        if state:
            raise MpdNotImplemented # TODO
        else:
            raise MpdNotImplemented # TODO

    @handle_pattern(r'^stats$')
    def _stats(self):
        """
        *musicpd.org, status section:*

            ``stats``

            Displays statistics.

            - ``artists``: number of artists
            - ``songs``: number of albums
            - ``uptime``: daemon uptime in seconds
            - ``db_playtime``: sum of all song times in the db
            - ``db_update``: last db update in UNIX time
            - ``playtime``: time length of music played
        """
        return {
            'artists': 0, # TODO
            'albums': 0, # TODO
            'songs': 0, # TODO
            'uptime': self.session.stats_uptime(),
            'db_playtime': 0, # TODO
            'db_update': 0, # TODO
            'playtime': 0, # TODO
        }

    @handle_pattern(r'^stop$')
    def _stop(self):
        """
        *musicpd.org, playback section:*

            ``stop``

            Stops playing.
        """
        self.backend.playback.stop()

    @handle_pattern(r'^status$')
    def _status(self):
        """
        *musicpd.org, status section:*

            ``status``

            Reports the current status of the player and the volume level.

            - ``volume``: 0-100
            - ``repeat``: 0 or 1
            - ``single``: 0 or 1
            - ``consume``: 0 or 1
            - ``playlist``: 31-bit unsigned integer, the playlist version
              number
            - ``playlistlength``: integer, the length of the playlist
            - ``state``: play, stop, or pause
            - ``song``: playlist song number of the current song stopped on or
              playing
            - ``songid``: playlist songid of the current song stopped on or
              playing
            - ``nextsong``: playlist song number of the next song to be played
            - ``nextsongid``: playlist songid of the next song to be played
            - ``time``: total time elapsed (of current playing/paused song)
            - ``elapsed``: Total time elapsed within the current song, but with
              higher resolution.
            - ``bitrate``: instantaneous bitrate in kbps
            - ``xfade``: crossfade in seconds
            - ``audio``: sampleRate``:bits``:channels
            - ``updatings_db``: job id
            - ``error``: if there is an error, returns message here
        """
        result = [
            ('volume', self._status_volume()),
            ('repeat', self._status_repeat()),
            ('random', self._status_random()),
            ('single', self._status_single()),
            ('consume', self._status_consume()),
            ('playlist', self._status_playlist_version()),
            ('playlistlength', self._status_playlist_length()),
            ('xfade', self._status_xfade()),
            ('state', self._status_state()),
        ]
        if self.backend.playback.current_track is not None:
            result.append(('song', self._status_songpos()))
            result.append(('songid', self._status_songid()))
        if self.backend.playback.state in (
                self.backend.playback.PLAYING, self.backend.playback.PAUSED):
            result.append(('time', self._status_time()))
            # TODO Add 'elapsed' here when moving to MPD 0.16.0
            result.append(('bitrate', self._status_bitrate()))
        return result

    def _status_bitrate(self):
        if self.backend.playback.current_track is not None:
            return self.backend.playback.current_track.bitrate

    def _status_consume(self):
        if self.backend.playback.consume:
            return 1
        else:
            return 0

    def _status_playlist_length(self):
        return self.backend.current_playlist.playlist.length

    def _status_playlist_version(self):
        return self.backend.current_playlist.version

    def _status_random(self):
        if self.backend.playback.random:
            return 1
        else:
            return 0

    def _status_repeat(self):
        if self.backend.playback.repeat:
            return 1
        else:
            return 0

    def _status_single(self):
        return 0 # TODO

    def _status_songid(self):
        if self.backend.playback.current_track.id is not None:
            return self.backend.playback.current_track.id
        else:
            return self._status_songpos()

    def _status_songpos(self):
        return self.backend.playback.playlist_position

    def _status_state(self):
        if self.backend.playback.state == self.backend.playback.PLAYING:
            return u'play'
        elif self.backend.playback.state == self.backend.playback.STOPPED:
            return u'stop'
        elif self.backend.playback.state == self.backend.playback.PAUSED:
            return u'pause'

    def _status_time(self):
        return u'%s:%s' % (
            self._status_time_elapsed(), self._status_time_total())

    def _status_time_elapsed(self):
        return self.backend.playback.time_position

    def _status_time_total(self):
        if self.backend.playback.current_track is None:
            return 0
        elif self.backend.playback.current_track.length is None:
            return 0
        else:
            return self.backend.playback.current_track.length // 1000

    def _status_volume(self):
        if self.backend.playback.volume is not None:
            return self.backend.playback.volume
        else:
            return 0

    def _status_xfade(self):
        return 0 # TODO

    @handle_pattern(r'^sticker delete "(?P<type>[^"]+)" "(?P<uri>[^"]+)"( "(?P<name>[^"]+)")*$')
    def _sticker_delete(self, type, uri, name=None):
        """
        *musicpd.org, sticker section:*

            ``sticker delete {TYPE} {URI} [NAME]``

            Deletes a sticker value from the specified object. If you do not
            specify a sticker name, all sticker values are deleted.
        """
        raise MpdNotImplemented # TODO

    @handle_pattern(r'^sticker find "(?P<type>[^"]+)" "(?P<uri>[^"]+)" "(?P<name>[^"]+)"$')
    def _sticker_find(self, type, uri, name):
        """
        *musicpd.org, sticker section:*

            ``sticker find {TYPE} {URI} {NAME}``

            Searches the sticker database for stickers with the specified name,
            below the specified directory (``URI``). For each matching song, it
            prints the ``URI`` and that one sticker's value.
        """
        raise MpdNotImplemented # TODO

    @handle_pattern(r'^sticker get "(?P<type>[^"]+)" "(?P<uri>[^"]+)" "(?P<name>[^"]+)"$')
    def _sticker_get(self, type, uri, name):
        """
        *musicpd.org, sticker section:*

            ``sticker get {TYPE} {URI} {NAME}``

            Reads a sticker value for the specified object.
        """
        raise MpdNotImplemented # TODO

    @handle_pattern(r'^sticker list "(?P<type>[^"]+)" "(?P<uri>[^"]+)"$')
    def _sticker_list(self, type, uri):
        """
        *musicpd.org, sticker section:*

            ``sticker list {TYPE} {URI}``

            Lists the stickers for the specified object.
        """
        raise MpdNotImplemented # TODO

    @handle_pattern(r'^sticker set "(?P<type>[^"]+)" "(?P<uri>[^"]+)" "(?P<name>[^"]+)" "(?P<value>[^"]+)"$')
    def _sticker_set(self, type, uri, name, value):
        """
        *musicpd.org, sticker section:*

            ``sticker set {TYPE} {URI} {NAME} {VALUE}``

            Adds a sticker value to the specified object. If a sticker item
            with that name already exists, it is replaced.
        """
        raise MpdNotImplemented # TODO

    @handle_pattern(r'^swap "(?P<songpos1>\d+)" "(?P<songpos2>\d+)"$')
    def _swap(self, songpos1, songpos2):
        """
        *musicpd.org, current playlist section:*

            ``swap {SONG1} {SONG2}``

            Swaps the positions of ``SONG1`` and ``SONG2``.
        """
        raise MpdNotImplemented # TODO

    @handle_pattern(r'^swapid "(?P<songid1>\d+)" "(?P<songid2>\d+)"$')
    def _swapid(self, songid1, songid2):
        """
        *musicpd.org, current playlist section:*

            ``swapid {SONG1} {SONG2}``

            Swaps the positions of ``SONG1`` and ``SONG2`` (both song ids).
        """
        raise MpdNotImplemented # TODO

    @handle_pattern(r'^tagtypes$')
    def _tagtypes(self):
        """
        *musicpd.org, reflection section:*

            ``tagtypes``

            Shows a list of available song metadata.
        """
        raise MpdNotImplemented # TODO

    @handle_pattern(r'^update( "(?P<uri>[^"]+)")*$')
    def _update(self, uri=None, rescan_unmodified_files=False):
        """
        *musicpd.org, music database section:*

            ``update [URI]``

            Updates the music database: find new files, remove deleted files,
            update modified files.

            ``URI`` is a particular directory or song/file to update. If you do
            not specify it, everything is updated.

            Prints ``updating_db: JOBID`` where ``JOBID`` is a positive number
            identifying the update job. You can read the current job id in the
            ``status`` response.
        """
        return {'updating_db': 0} # TODO

    @handle_pattern(r'^urlhandlers$')
    def _urlhandlers(self):
        """
        *musicpd.org, reflection section:*

            ``urlhandlers``

            Gets a list of available URL handlers.
        """
        return self.backend.uri_handlers
