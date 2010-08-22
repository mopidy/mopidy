def populate_playlist(func):
    def wrapper(self):
        for track in self.tracks:
            self.backend.current_playlist.add(track)
        return func(self)

    wrapper.__name__ = func.__name__
    wrapper.__doc__ = func.__doc__
    return wrapper
