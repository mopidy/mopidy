************
Frontend API
************

A frontend may do whatever it wants to, including creating threads, opening TCP
ports and exposing Mopidy for a type of clients.

Frontends got one main limitation: they are restricted to passing messages
through the ``core_queue`` for all communication with the rest of Mopidy. Thus,
the frontend API is very small and reveals little of what a frontend may do.

.. warning::

    A stable frontend API is not available yet, as we've only implemented a
    couple of frontend modules.

.. automodule:: mopidy.frontends.base
    :synopsis: Base class for frontends
    :members:


Frontend implementations
========================

* :mod:`mopidy.frontends.lastfm`
* :mod:`mopidy.frontends.mpd`
