import os


# FIXME replace with mock usage in tests.
class Mtime:
    def __init__(self):
        self.fake = None

    def __call__(self, path):
        if self.fake is not None:
            return self.fake
        return int(os.stat(path).st_mtime)

    def set_fake_time(self, time):
        self.fake = time

    def undo_fake(self):
        self.fake = None


mtime = Mtime()
