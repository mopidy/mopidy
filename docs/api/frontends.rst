.. _frontend-api:

************
Frontend API
************

The following requirements applies to any frontend implementation:

- A frontend MAY do mostly whatever it wants to, including creating threads,
  opening TCP ports and exposing Mopidy for a group of clients.

- A frontend MUST implement at least one `Pykka
  <http://pykka.readthedocs.org/>`_ actor, called the "main actor" from here
  on.

- The main actor MUST accept a constructor argument ``core``, which will be an
  :class:`ActorProxy <pykka.proxy.ActorProxy>` for the core actor. This object
  gives access to the full :ref:`core-api`.

- It MAY use additional actors to implement whatever it does, and using actors
  in frontend implementations is encouraged.

- The frontend is activated by including its main actor in the
  :attr:`mopidy.settings.FRONTENDS` setting.

- The main actor MUST be able to start and stop the frontend when the main
  actor is started and stopped.

- The frontend MAY require additional settings to be set for it to
  work.

- Such settings MUST be documented.

- The main actor MUST stop itself if the defined settings are not adequate for
  the frontend to work properly.

- Any actor which is part of the frontend MAY implement the
  :class:`mopidy.core.CoreListener` interface to receive notification of the
  specified events.


.. _frontend-implementations:

Frontend implementations
========================

* :mod:`mopidy.frontends.http`
* :mod:`mopidy.frontends.lastfm`
* :mod:`mopidy.frontends.mpd`
* :mod:`mopidy.frontends.mpris`
