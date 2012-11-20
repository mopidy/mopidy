from __future__ import unicode_literals


def populate_tracklist(func):
    def wrapper(self):
        self.tl_tracks = []
        for track in self.tracks:
            self.tl_tracks.append(self.core.tracklist.add(track))
        return func(self)

    wrapper.__name__ = func.__name__
    wrapper.__doc__ = func.__doc__
    return wrapper
