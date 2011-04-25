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

def path_to_data_dir(name):
    path = os.path.dirname(__file__)
    path = os.path.join(path, 'data')
    path = os.path.abspath(path)
    return os.path.join(path, name)

