**************
Running Mopidy
**************

To start Mopidy, simply open a terminal and run::

    mopidy

When Mopidy says ``MPD server running at [127.0.0.1]:6600`` it's ready to
accept connections by any MPD client. Check out our non-exhaustive
:doc:`/clients/mpd` list to find recommended clients.

To stop Mopidy, press ``CTRL+C`` in the terminal where you started Mopidy.

Mopidy will also shut down properly if you send it the TERM signal, e.g. by
using ``kill``::

    kill `ps ax | grep mopidy | grep -v grep | cut -d' ' -f1`

This can be useful e.g. if you create init script for managing Mopidy.
