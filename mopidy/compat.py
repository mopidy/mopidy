import inspect


def getargspec(func):
    spec = inspect.getfullargspec(func)
    return inspect.ArgSpec(spec.args, spec.varargs, spec.varkw, spec.defaults)


def getcallargs(func, *args, **kwargs):
    ba = inspect.signature(func).bind(*args, **kwargs)
    ba.apply_defaults()
    return ba.arguments
