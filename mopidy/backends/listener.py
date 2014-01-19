from __future__ import unicode_literals

from mopidy.backend import BackendListener


# Make classes previously residing here available in the old location for
# backwards compatibility with extensions targeting Mopidy < 0.18.
__all__ = ['BackendListener']
