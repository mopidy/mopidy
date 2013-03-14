from __future__ import unicode_literals

import logging
import pykka

from mopidy import settings
from mopidy.backends import base


from .library import SoundcloudLibraryProvider
from .playlists import SoundcloudPlaylistsProvider
from .soundcloud import SoundcloudClient

logger = logging.getLogger('mopidy.backends.soundcloud')


class SoundcloudBackend(pykka.ThreadingActor, base.Backend):
    def __init__(self, audio):
        super(SoundcloudBackend, self).__init__()

        self.sc_api = SoundcloudClient(settings.SOUNDCLOUD_USERNAME)

        self.library = SoundcloudLibraryProvider(backend=self)
        self.playback = base.BasePlaybackProvider(audio=audio, backend=self)
        self.playlists = SoundcloudPlaylistsProvider(backend=self)

        self.uri_schemes = ['soundcloud']
