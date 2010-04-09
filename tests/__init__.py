try: # 2.7
    from unittest.case import SkipTest
except ImportError:
    try: # Nose
        from nose.plugins.skip import SkipTest
    except ImportError: # Failsafe
        class SkipTest(Exception):
            pass
