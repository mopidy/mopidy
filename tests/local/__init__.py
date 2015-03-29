from __future__ import absolute_import, unicode_literals

import warnings


def generate_song(i):
    return 'local:track:song%s.wav' % i


def populate_tracklist(func):
    def wrapper(self):
        with warnings.catch_warnings():
            warnings.filterwarnings('ignore', 'tracklist.add.*"tracks".*')
            self.tl_tracks = self.core.tracklist.add(self.tracks)
        return func(self)

    wrapper.__name__ = func.__name__
    wrapper.__doc__ = func.__doc__
    return wrapper
