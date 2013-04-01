from __future__ import unicode_literals

import mopidy
from mopidy import ext
from mopidy.exceptions import ExtensionError


__doc__ = """
Frontend which scrobbles the music you play to your `Last.fm
<http://www.last.fm>`_ profile.

.. note::

    This frontend requires a free user account at Last.fm.

**Dependencies:**

.. literalinclude:: ../../../requirements/lastfm.txt

**Settings:**

- :attr:`mopidy.settings.LASTFM_USERNAME`
- :attr:`mopidy.settings.LASTFM_PASSWORD`

**Usage:**

The frontend is enabled by default if all dependencies are available.
"""


class Extension(ext.Extension):

    name = 'Mopidy-Lastfm'
    version = mopidy.__version__

    def get_default_config(self):
        return '[ext.lastfm]'

    def validate_config(self, config):
        pass

    def validate_environment(self):
        try:
            import pylast  # noqa
        except ImportError as e:
            raise ExtensionError('pylast library not found', e)

    def get_frontend_classes(self):
        from .actor import LastfmFrontend
        return [LastfmFrontend]
