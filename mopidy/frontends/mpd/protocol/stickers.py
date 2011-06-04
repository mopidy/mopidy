from mopidy.frontends.mpd.protocol import handle_request
from mopidy.frontends.mpd.exceptions import MpdNotImplemented

@handle_request(r'^sticker delete "(?P<field>[^"]+)" '
    r'"(?P<uri>[^"]+)"( "(?P<name>[^"]+)")*$')
def sticker_delete(context, field, uri, name=None):
    """
    *musicpd.org, sticker section:*

        ``sticker delete {TYPE} {URI} [NAME]``

        Deletes a sticker value from the specified object. If you do not
        specify a sticker name, all sticker values are deleted.
    """
    raise MpdNotImplemented # TODO

@handle_request(r'^sticker find "(?P<field>[^"]+)" "(?P<uri>[^"]+)" '
    r'"(?P<name>[^"]+)"$')
def sticker_find(context, field, uri, name):
    """
    *musicpd.org, sticker section:*

        ``sticker find {TYPE} {URI} {NAME}``

        Searches the sticker database for stickers with the specified name,
        below the specified directory (``URI``). For each matching song, it
        prints the ``URI`` and that one sticker's value.
    """
    raise MpdNotImplemented # TODO

@handle_request(r'^sticker get "(?P<field>[^"]+)" "(?P<uri>[^"]+)" '
    r'"(?P<name>[^"]+)"$')
def sticker_get(context, field, uri, name):
    """
    *musicpd.org, sticker section:*

        ``sticker get {TYPE} {URI} {NAME}``

        Reads a sticker value for the specified object.
    """
    raise MpdNotImplemented # TODO

@handle_request(r'^sticker list "(?P<field>[^"]+)" "(?P<uri>[^"]+)"$')
def sticker_list(context, field, uri):
    """
    *musicpd.org, sticker section:*

        ``sticker list {TYPE} {URI}``

        Lists the stickers for the specified object.
    """
    raise MpdNotImplemented # TODO

@handle_request(r'^sticker set "(?P<field>[^"]+)" "(?P<uri>[^"]+)" '
    r'"(?P<name>[^"]+)" "(?P<value>[^"]+)"$')
def sticker_set(context, field, uri, name, value):
    """
    *musicpd.org, sticker section:*

        ``sticker set {TYPE} {URI} {NAME} {VALUE}``

        Adds a sticker value to the specified object. If a sticker item
        with that name already exists, it is replaced.
    """
    raise MpdNotImplemented # TODO
