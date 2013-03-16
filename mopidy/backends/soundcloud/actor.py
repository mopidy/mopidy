from __future__ import unicode_literals

import logging
import pykka

from mopidy import settings
from mopidy.backends import base


from .library import SoundcloudLibraryProvider
from .playlists import SoundcloudPlaylistsProvider
from .soundcloud import SoundCloudClient

logger = logging.getLogger('mopidy.backends.soundcloud')


class SoundcloudBackend(pykka.ThreadingActor, base.Backend):
    def __init__(self, audio):
        super(SoundcloudBackend, self).__init__()

        if not settings.SOUNDCLOUD_AUTHTOKEN:
            logger.error(("In order to use SoundCloud backend "
                          "you must provide settings.SOUNDCLOUD_AUTHTOKEN. "
                          "Get yours at http://www.mopidy.com/authenticate.html"))
        else:
            self.sc_api = SoundCloudClient(
                settings.SOUNDCLOUD_AUTHTOKEN)

        self.library = SoundcloudLibraryProvider(backend=self)
        self.playback = base.BasePlaybackProvider(audio=audio, backend=self)
        self.playlists = SoundcloudPlaylistsProvider(backend=self)

        self.uri_schemes = ['soundcloud']
