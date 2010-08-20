import os
import sys

# Add ../ to the path so we can run Mopidy from a Git checkout without
# installing it on the system.
sys.path.insert(0,
    os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

from mopidy.core import CoreProcess

if __name__ == '__main__':
    # Explictly call run() instead of start(), since we don't need to start
    # another process.
    CoreProcess().run()
