********
Glossary
********

.. glossary::

    backend
        A part of Mopidy providing music library, playlist storage and/or
        playback capability to the :term:`core`. Mopidy has a backend for each
        music store or music service it supports. See :ref:`backend-api` for
        details.

    core
        The part of Mopidy that makes multiple frontends capable of using
        multiple backends. The core module is also the owner of the
        :term:`tracklist`. To use the core module, see :ref:`core-api`.

    extension
        A Python package that can extend Mopidy with one or more
        :term:`backends <backend>`, :term:`frontends <frontend>`,
        :term:`mixers <mixer>`, or web clients.
        See the `extension registry <https://mopidy.com/ext/>`_ for available
        Mopidy extensions.
        See :ref:`extensiondev` for how to make a new extension.

    frontend
        A part of Mopidy *using* the :term:`core` API. Existing frontends
        include the MPD server, the MPRIS/D-Bus integration,
        the Last.fm scrobbler, and the :ref:`HTTP server <ext-http>`.
        See :ref:`frontend-api` for details.

    mixer
        A part of Mopidy that controls audio volume and muting.

    tracklist
        Mopidy's name for the play queue or current playlist. The name is
        inspired by the MPRIS specification.
