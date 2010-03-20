*********
Internals
*********

Some of the following notes and details will hopefully be useful when you start
developing on Mopidy, while some may only be useful when you get deeper into
specific parts of Mopidy.

In addition to what you'll find here, don't forget the :doc:`/api/index`.


Class instantiation and usage
=============================

The following diagram shows how Mopidy with the despotify backend and ALSA
mixer is wired together. The gray nodes are part of external dependencies, and
not Mopidy. The red nodes lives in the ``main`` process (running an
:mod:`asyncore` loop), while the blue nodes lives in a secondary process named
``core`` (running a service loop in :class:`mopidy.core.CoreProcess`).

.. digraph:: class_instantiation_and_usage

    "spytify" [ color="gray" ]
    "despotify" [ color="gray" ]
    "alsaaudio" [ color="gray" ]
    "__main__" [ color="red" ]
    "CoreProcess" [ color="blue" ]
    "DespotifyBackend" [ color="blue" ]
    "AlsaMixer" [ color="blue" ]
    "MpdHandler" [ color="blue" ]
    "MpdServer" [ color="red" ]
    "MpdSession" [ color="red" ]
    "__main__" -> "CoreProcess" [ label="create" ]
    "__main__" -> "MpdServer" [ label="create" ]
    "CoreProcess" -> "DespotifyBackend" [ label="create" ]
    "CoreProcess" -> "MpdHandler" [ label="create" ]
    "MpdServer" -> "MpdSession" [ label="create one per client" ]
    "MpdSession" -> "MpdHandler" [ label="pass MPD requests to" ]
    "MpdHandler" -> "DespotifyBackend" [ label="use backend API" ]
    "DespotifyBackend" -> "AlsaMixer" [ label="create and use mixer API" ]
    "DespotifyBackend" -> "spytify" [ label="use Python wrapper" ]
    "spytify" -> "despotify" [ label="use C library" ]
    "AlsaMixer" -> "alsaaudio" [ label="use Python library" ]


Thread communication
====================

.. warning::

    This is a plan, and does not necessarily reflect what has been implemented.

.. image:: /_static/thread_communication.png
