import logging
import os
import sys

from CoverageTestRunner import CoverageTestRunner

def main():
    logging.basicConfig(level=logging.CRITICAL)
    sys.path.insert(0,
        os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))
    r = CoverageTestRunner()
    r.add_pair('mopidy/mixers/dummy.py', 'tests/mixers/dummytest.py')
    r.add_pair('mopidy/mixers/denon.py', 'tests/mixers/denontest.py')
    r.add_pair('mopidy/models.py', 'tests/modelstest.py')
    r.add_pair('mopidy/mpd/handler.py', 'tests/mpd/handlertest.py')
    r.run()

if __name__ == '__main__':
    main()
