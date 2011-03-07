# Add ../ to the path so we can run Mopidy from a Git checkout without
# installing it on the system.
import os
import sys
sys.path.insert(0,
    os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

if __name__ == '__main__':
    from mopidy.core import main
    main()
