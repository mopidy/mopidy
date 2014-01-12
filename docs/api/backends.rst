.. _backend-api:

***********
Backend API
***********

.. module:: mopidy.backend
    :synopsis: The API implemented by backends

The backend API is the interface that must be implemented when you create a
backend. If you are working on a frontend and need to access the backends, see
the :ref:`core-api` instead.


Backend class
=============

.. autoclass:: mopidy.backend.Backend
    :members:


Playback provider
=================

.. autoclass:: mopidy.backend.PlaybackProvider
    :members:


Playlists provider
==================

.. autoclass:: mopidy.backend.PlaylistsProvider
    :members:


Library provider
================

.. autoclass:: mopidy.backend.LibraryProvider
    :members:


Backend listener
================

.. autoclass:: mopidy.backend.BackendListener
    :members:


.. _backend-implementations:

Backend implementations
=======================

- `Mopidy-Beets <https://github.com/mopidy/mopidy-beets>`_

- `Mopidy-GMusic <https://github.com/hechtus/mopidy-gmusic>`_

- :ref:`ext-local`

- `Mopidy-radio-de <https://github.com/hechtus/mopidy-radio-de>`_

- `Mopidy-SomaFM <https://github.com/AlexandrePTJ/mopidy-somafm>`_

- `Mopidy-SoundCloud <https://github.com/mopidy/mopidy-soundcloud>`_

- `Mopidy-Spotify <https://github.com/mopidy/mopidy-spotify>`_

- :ref:`ext-stream`

- `Mopidy-Subsonic <https://github.com/rattboi/mopidy-subsonic>`_

- `Mopidy-VKontakte <https://github.com/sibuser/mopidy-vkontakte>`_
