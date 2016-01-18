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

Updating the library
====================

To update the library, e.g. after audio files have changed, run::

    mopidy local scan

Afterwards, to refresh the library (which is for now only available
through the API) it is necessary to run::

    curl -d '{"jsonrpc": "2.0", "id": 1, "method": "core.library.refresh"}' http://localhost:6680/mopidy/rpc

This makes the changes in the library visible to the clients.


Stopping Mopidy
===============

To stop Mopidy, press ``CTRL+C`` in the terminal where you started Mopidy.

Mopidy will also shut down properly if you send it the TERM signal, e.g. by
using ``pkill``::

    pkill mopidy


Running as a service
====================

Once you're done exploring Mopidy and want to run it as a proper service, check
out :ref:`service`.
