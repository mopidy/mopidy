import pathlib


def path_to_data_dir(name):
    path = pathlib.Path(__file__).parent / "data" / name
    return path.resolve()


class IsA:
    def __init__(self, klass):
        self.klass = klass

    def __eq__(self, rhs):
        try:
            return isinstance(rhs, self.klass)
        except TypeError:
            return type(rhs) == type(self.klass)  # noqa

    def __ne__(self, rhs):
        return not self.__eq__(rhs)

    def __repr__(self):
        return str(self.klass)


any_int = IsA(int)
any_str = IsA(str)
any_unicode = any_str  # TODO remove
