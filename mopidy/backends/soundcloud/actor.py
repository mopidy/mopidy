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
            self.playback = SoundCloudPlaybackProvider(audio=audio, backend=self)
            self.playlists = SoundCloudPlaylistsProvider(backend=self)

            self.uri_schemes = ['soundcloud']


class SoundCloudPlaybackProvider(base.BasePlaybackProvider):

    def play(self, track):
        id = track.uri.split(';')[1]
        logger.info('Getting info for track %s with id %s' % (track.uri, id))
        track = self.backend.sc_api.get_track(id, True)
        return super(SoundCloudPlaybackProvider, self).play(track)
