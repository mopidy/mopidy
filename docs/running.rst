**************
Running Mopidy
**************

To start Mopidy, simply open a terminal and run::

    mopidy

For a complete reference to the Mopidy commands and their command line options,
see :ref:`mopidy-cmd`.

When Mopidy says ``MPD server running at [127.0.0.1]:6600`` it's ready to
accept connections by any MPD client. Check out our non-exhaustive
:doc:`/clients/mpd` list to find recommended clients.


Stopping Mopidy
===============

To stop Mopidy, press ``CTRL+C`` in the terminal where you started Mopidy.

Mopidy will also shut down properly if you send it the TERM signal, e.g. by
using ``pkill``::

    pkill mopidy

