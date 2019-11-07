import inspect
import sys

PY2 = sys.version_info[0] == 2
PY3 = sys.version_info[0] == 3

integer_types = (int,)
string_types = (str,)
text_type = str
text_prefix = ""  # noqa

input = input
intern = sys.intern


def itervalues(dct, **kwargs):
    return iter(dct.values(**kwargs))


def iteritems(dct, **kwargs):
    return iter(dct.items(**kwargs))


def getargspec(func):
    spec = inspect.getfullargspec(func)
    return inspect.ArgSpec(spec.args, spec.varargs, spec.varkw, spec.defaults)


def getcallargs(func, *args, **kwargs):
    ba = inspect.signature(func).bind(*args, **kwargs)
    ba.apply_defaults()
    return ba.arguments


def add_metaclass(metaclass):
    """Class decorator for creating a class with a metaclass."""

    def wrapper(cls):
        orig_vars = cls.__dict__.copy()
        slots = orig_vars.get("__slots__")
        if slots is not None:
            if isinstance(slots, str):
                slots = [slots]
            for slots_var in slots:
                orig_vars.pop(slots_var)
        orig_vars.pop("__dict__", None)
        orig_vars.pop("__weakref__", None)
        if hasattr(cls, "__qualname__"):
            orig_vars["__qualname__"] = cls.__qualname__
        return metaclass(cls.__name__, cls.__bases__, orig_vars)

    return wrapper
