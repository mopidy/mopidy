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

- The main actor MUST accept two constructor arguments:

  - ``config``, which is a dict structure with the entire Mopidy configuration.

  - ``core``, which will be an :class:`ActorProxy <pykka.proxy.ActorProxy>` for
    the core actor. This object gives access to the full :ref:`core-api`.

- It MAY use additional actors to implement whatever it does, and using actors
  in frontend implementations is encouraged.

- The frontend is enabled if the extension it is part of is enabled. See
  :ref:`extensiondev` for more information.

- The main actor MUST be able to start and stop the frontend when the main
  actor is started and stopped.

- The frontend MAY require additional config values to be set for it to work.

- Such config values MUST be documented.

- The main actor MUST raise the :exc:`mopidy.exceptions.FrontendError` with a
  descriptive error message if the defined config values are not adequate for
  the frontend to work properly.

- Any actor which is part of the frontend MAY implement the
  :class:`mopidy.core.CoreListener` interface to receive notification of the
  specified events.


Frontend implementations
========================

See :ref:`ext-frontends`.
