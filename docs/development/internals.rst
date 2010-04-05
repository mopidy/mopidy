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
    "MpdFrontend" [ color="blue" ]
    "MpdServer" [ color="red" ]
    "MpdSession" [ color="red" ]
    "__main__" -> "CoreProcess" [ label="create" ]
    "__main__" -> "MpdServer" [ label="create" ]
    "CoreProcess" -> "DespotifyBackend" [ label="create" ]
    "CoreProcess" -> "MpdFrontend" [ label="create" ]
    "MpdServer" -> "MpdSession" [ label="create one per client" ]
    "MpdSession" -> "MpdFrontend" [ label="pass MPD requests to" ]
    "MpdFrontend" -> "DespotifyBackend" [ label="use backend API" ]
    "DespotifyBackend" -> "AlsaMixer" [ label="create and use mixer API" ]
    "DespotifyBackend" -> "spytify" [ label="use Python wrapper" ]
    "spytify" -> "despotify" [ label="use C library" ]
    "AlsaMixer" -> "alsaaudio" [ label="use Python library" ]


Thread/process communication
============================

- Everything starts with ``Main``.
- ``Main`` creates a ``Core`` process which runs the frontend, backend, and
  mixer.
- Mixers *may* create an additional process for communication with external
  devices, like ``NadTalker`` in this example.
- Backend libraries *may* have threads of their own, like ``despotify`` here
  which has additional threads in the ``Core`` process.
- ``Server`` part currently runs in the same process and thread as ``Main``.
- ``Client`` is some external client talking to ``Server`` over a socket.

.. image:: /_static/thread_communication.png
