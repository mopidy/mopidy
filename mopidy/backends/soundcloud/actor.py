from __future__ import unicode_literals

import logging
import pykka

from mopidy import settings
from mopidy.backends import base


from .library import SoundCloudLibraryProvider
from .playlists import SoundCloudPlaylistsProvider
from .soundcloud import SoundCloudClient

logger = logging.getLogger('mopidy.backends.soundcloud')


class SoundCloudBackend(pykka.ThreadingActor, base.Backend):
    def __init__(self, audio):
        super(SoundCloudBackend, self).__init__()

        if not settings.SOUNDCLOUD_AUTH_TOKEN:
            logger.error(("In order to use SoundCloud backend "
                          "you must provide settings.SOUNDCLOUD_AUTH_TOKEN. "
                          "Get yours at http://www.mopidy.com/authenticate"))
        else:
            self.sc_api = SoundCloudClient(settings.SOUNDCLOUD_AUTH_TOKEN)
            self.library = SoundCloudLibraryProvider(backend=self)
            self.playback = base.BasePlaybackProvider(audio=audio, backend=self)
            self.playlists = SoundCloudPlaylistsProvider(backend=self)

            self.uri_schemes = ['soundcloud']
