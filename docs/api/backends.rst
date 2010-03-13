**********************
:mod:`mopidy.backends`
**********************

The backend and its controllers
===============================

.. graph:: backend_relations

    backend -- current_playlist
    backend -- library
    backend -- playback
    backend -- stored_playlists


Backend API
===========

.. note::

    Currently this only documents the API that is available for use by
    frontends like :class:`mopidy.mpd.handler`, and not what is required to
    implement your own backend. :class:`mopidy.backends.BaseBackend` and its
    controllers implements many of these methods in a matter that should be
    independent of most concrete backend implementations, so you should
    generally just implement or override a few of these methods yourself to
    create a new backend with a complete feature set.

.. automodule:: mopidy.backends
    :synopsis: Backend interface.
    :members:
    :undoc-members:


Spotify backends
================

:mod:`mopidy.backends.despotify` -- Despotify backend
-----------------------------------------------------

.. automodule:: mopidy.backends.despotify
    :synopsis: Spotify backend using the despotify library.
    :members:


:mod:`mopidy.backends.libspotify` -- Libspotify backend
-------------------------------------------------------

.. automodule:: mopidy.backends.libspotify
    :synopsis: Spotify backend using the libspotify library.
    :members:


Other backends
==============

:mod:`mopidy.backends.dummy` -- Dummy backend
---------------------------------------------

.. automodule:: mopidy.backends.dummy
    :synopsis: Dummy backend used for testing.
    :members:


GStreamer backend
-----------------

``GstreamerBackend`` is pending merge from `adamcik/mopidy/gstreamer
<http://github.com/adamcik/mopidy/tree/gstreamer>`_.
