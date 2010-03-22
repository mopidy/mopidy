import os

from mopidy.settings.default import *
from mopidy.utils import get_or_create_dotdir

dotdir = get_or_create_dotdir()
settings_file = os.path.join(dotdir, u'settings.py')
if not os.path.isfile(settings_file):
    logger.warning(u'Settings not found: %s', settings_file)
else:
    sys.path.insert(0, dotdir)
    from settings import *
