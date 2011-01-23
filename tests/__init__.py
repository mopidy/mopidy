import os

try: # 2.7
    # pylint: disable = E0611,F0401
    from unittest.case import SkipTest
    # pylint: enable = E0611,F0401
except ImportError:
    try: # Nose
        from nose.plugins.skip import SkipTest
    except ImportError: # Failsafe
        class SkipTest(Exception):
            pass

from mopidy import settings

# Nuke any local settings to ensure same test env all over
settings.local.clear()

def data_folder(name):
    folder = os.path.dirname(__file__)
    folder = os.path.join(folder, 'data')
    folder = os.path.abspath(folder)
    return os.path.join(folder, name)

