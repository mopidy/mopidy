from __future__ import unicode_literals

from distutils.version import StrictVersion as SV
import sys
import warnings

import pykka


if not (2, 7) <= sys.version_info < (3,):
    sys.exit(
        'Mopidy requires Python >= 2.7, < 3, but found %s' %
        '.'.join(map(str, sys.version_info[:3])))

if (isinstance(pykka.__version__, basestring)
        and not SV('1.1') <= SV(pykka.__version__) < SV('2.0')):
    sys.exit(
        'Mopidy requires Pykka >= 1.1, < 2, but found %s' % pykka.__version__)


warnings.filterwarnings('ignore', 'could not open display')


__version__ = '0.17.0a1'
