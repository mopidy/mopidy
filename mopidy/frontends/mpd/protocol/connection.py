from mopidy.frontends.mpd import handle_pattern, MpdNotImplemented

@handle_pattern(r'^close$')
def close(frontend):
    """
    *musicpd.org, connection section:*

        ``close``

        Closes the connection to MPD.
    """
    # TODO Does not work after multiprocessing branch merge
    #frontend.session.do_close()

@handle_pattern(r'^kill$')
def kill(frontend):
    """
    *musicpd.org, connection section:*

        ``kill``

        Kills MPD.
    """
    # TODO Does not work after multiprocessing branch merge
    #frontend.session.do_kill()

@handle_pattern(r'^password "(?P<password>[^"]+)"$')
def password_(frontend, password):
    """
    *musicpd.org, connection section:*

        ``password {PASSWORD}``

        This is used for authentication with the server. ``PASSWORD`` is
        simply the plaintext password.
    """
    raise MpdNotImplemented # TODO

@handle_pattern(r'^ping$')
def ping(frontend):
    """
    *musicpd.org, connection section:*

        ``ping``

        Does nothing but return ``OK``.
    """
    pass
