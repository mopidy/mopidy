import logging
import os
import sys

from CoverageTestRunner import CoverageTestRunner

def main():
    logging.basicConfig(level=logging.CRITICAL)
    sys.path.insert(0,
        os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))
    r = CoverageTestRunner()
    r.add_pair('mopidy/handler.py', 'tests/handlertest.py')
    r.run()

if __name__ == '__main__':
    main()
