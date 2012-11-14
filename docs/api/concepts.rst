.. _concepts:

*************************
Architecture and concepts
*************************

The overall architecture of Mopidy is organized around multiple frontends and
backends. The frontends use the core API. The core actor makes multiple backends
work as one. The backends connect to various music sources. Both the core actor
and the backends use the audio actor to play audio and control audio volume.

.. digraph:: overall_architecture

    "Multiple frontends" -> Core
    Core -> "Multiple backends"
    Core -> Audio
    "Multiple backends" -> Audio


Frontends
=========

Frontends expose Mopidy to the external world. They can implement servers for
protocols like MPD and MPRIS, and they can be used to update other services
when something happens in Mopidy, like the Last.fm scrobbler frontend does. See
:ref:`frontend-api` for more details.

.. digraph:: frontend_architecture

    "MPD\nfrontend" -> Core
    "MPRIS\nfrontend" -> Core
    "Last.fm\nfrontend" -> Core


Core
====

The core is organized as a set of controllers with responsiblity for separate
sets of functionality.

The core is the single actor that the frontends send their requests to. For
every request from a frontend it calls out to one or more backends which does
the real work, and when the backends respond, the core actor is responsible for
combining the responses into a single response to the requesting frontend.

The core actor also keeps track of the tracklist, since it doesn't belong to a
specific backend.

See :ref:`core-api` for more details.

.. digraph:: core_architecture

    Core -> "Tracklist\ncontroller"
    Core -> "Library\ncontroller"
    Core -> "Playback\ncontroller"
    Core -> "Playlists\ncontroller"

    "Library\ncontroller" -> "Local backend"
    "Library\ncontroller" -> "Spotify backend"

    "Playback\ncontroller" -> "Local backend"
    "Playback\ncontroller" -> "Spotify backend"
    "Playback\ncontroller" -> Audio

    "Playlists\ncontroller" -> "Local backend"
    "Playlists\ncontroller" -> "Spotify backend"


Backends
========

The backends are organized as a set of providers with responsiblity for
separate sets of functionality, similar to the core actor.

Anything specific to i.e. Spotify integration or local storage is contained in
the backends. To integrate with new music sources, you just add a new backend.
See :ref:`backend-api` for more details.

.. digraph:: backend_architecture

    "Local backend" -> "Local\nlibrary\nprovider" -> "Local disk"
    "Local backend" -> "Local\nplayback\nprovider" -> "Local disk"
    "Local backend" -> "Local\nplaylists\nprovider" -> "Local disk"
    "Local\nplayback\nprovider" -> Audio

    "Spotify backend" -> "Spotify\nlibrary\nprovider" -> "Spotify service"
    "Spotify backend" -> "Spotify\nplayback\nprovider" -> "Spotify service"
    "Spotify backend" -> "Spotify\nplaylists\nprovider" -> "Spotify service"
    "Spotify\nplayback\nprovider" -> Audio


Audio
=====

The audio actor is a thin wrapper around the parts of the GStreamer library we
use. In addition to playback, it's responsible for volume control through both
GStreamer's own volume mixers, and mixers we've created ourselves. If you
implement an advanced backend, you may need to implement your own playback
provider using the :ref:`audio-api`.
