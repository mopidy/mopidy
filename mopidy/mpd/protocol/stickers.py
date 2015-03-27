from __future__ import absolute_import, unicode_literals

from mopidy.mpd import exceptions, protocol


@protocol.commands.add('sticker', list_command=False)
def sticker(context, action, field, uri, name=None, value=None):
    """
    *musicpd.org, sticker section:*

        ``sticker list {TYPE} {URI}``

        Lists the stickers for the specified object.

        ``sticker find {TYPE} {URI} {NAME}``

        Searches the sticker database for stickers with the specified name,
        below the specified directory (``URI``). For each matching song, it
        prints the ``URI`` and that one sticker's value.

        ``sticker get {TYPE} {URI} {NAME}``

        Reads a sticker value for the specified object.

        ``sticker set {TYPE} {URI} {NAME} {VALUE}``

        Adds a sticker value to the specified object. If a sticker item
        with that name already exists, it is replaced.

        ``sticker delete {TYPE} {URI} [NAME]``

        Deletes a sticker value from the specified object. If you do not
        specify a sticker name, all sticker values are deleted.

    """
    # TODO: check that action in ('list', 'find', 'get', 'set', 'delete')
    # TODO: check name/value matches with action
    raise exceptions.MpdNotImplemented  # TODO
