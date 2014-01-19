from __future__ import unicode_literals

from mopidy.backend import (
    Backend,
    LibraryProvider as BaseLibraryProvider,
    PlaybackProvider as BasePlaybackProvider,
    PlaylistsProvider as BasePlaylistsProvider)


# Make classes previously residing here available in the old location for
# backwards compatibility with extensions targeting Mopidy < 0.18.
__all__ = [
    'Backend',
    'BaseLibraryProvider',
    'BasePlaybackProvider',
    'BasePlaylistsProvider',
]
