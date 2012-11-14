from __future__ import unicode_literals

import nose
import yappi

try:
    yappi.start()
    nose.main()
finally:
    yappi.print_stats()
