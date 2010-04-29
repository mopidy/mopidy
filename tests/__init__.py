import os

try: # 2.7
    from unittest.case import SkipTest
except ImportError:
    try: # Nose
        from nose.plugins.skip import SkipTest
    except ImportError: # Failsafe
        class SkipTest(Exception):
            pass

def data_folder(name):
    folder = os.path.dirname(__file__)
    folder = os.path.join(folder, 'data')
    folder = os.path.abspath(folder)
    return os.path.join(folder, name)

