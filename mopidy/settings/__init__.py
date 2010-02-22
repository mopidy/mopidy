from mopidy.settings.default import *

try:
    from mopidy.settings.local import *
except ImportError:
    pass
