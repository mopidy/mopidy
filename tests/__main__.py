import nose
import yappi

try:
    yappi.start()
    nose.main()
finally:
    yappi.print_stats()
