.. _backend-concepts:

**********************************************
The backend, controller, and provider concepts
**********************************************

Backend:
    The backend is mostly for convenience. It is a container that holds
    references to all the controllers.
Controllers:
    Each controller has responsibility for a given part of the backend
    functionality. Most, but not all, controllers delegates some work to one or
    more providers. The controllers are responsible for choosing the right
    provider for any given task based upon i.e. the track's URI. See
    :ref:`backend-controller-api` for more details.
Providers:
    Anything specific to i.e. Spotify integration or local storage is contained
    in the providers. To integrate with new music sources, you just add new
    providers. See :ref:`backend-provider-api` for more details.

.. digraph:: backend_relations

    Backend -> "Current\nplaylist\ncontroller"
    Backend -> "Library\ncontroller"
    "Library\ncontroller" -> "Library\nproviders"
    Backend -> "Playback\ncontroller"
    "Playback\ncontroller" -> "Playback\nproviders"
    Backend -> "Stored\nplaylists\ncontroller"
    "Stored\nplaylists\ncontroller" -> "Stored\nplaylist\nproviders"
    Backend -> Mixer
