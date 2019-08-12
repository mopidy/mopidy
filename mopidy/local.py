# XXX This module is only here to ease the migration from Mopidy-Local being
# bundled with Mopidy to being an independent extension. This file should
# probably be removed before Mopidy 3.0 final ships.

import warnings

from mopidy_local import *  # noqa


warnings.warn(
    'Mopidy-Local has been moved to its own project. '
    'Update any imports from `mopidy.local` to use `mopidy_local` instead.',
    DeprecationWarning
)
