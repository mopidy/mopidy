from __future__ import unicode_literals

from mopidy.utils.path import path_to_uri


generate_song = lambda i: 'local:track:song%s.wav' % i
