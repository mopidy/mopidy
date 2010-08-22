*********
Internals
*********

Some of the following notes and details will hopefully be useful when you start
developing on Mopidy, while some may only be useful when you get deeper into
specific parts of Mopidy.

In addition to what you'll find here, don't forget the :doc:`/api/index`.


Class instantiation and usage
=============================

The following diagram shows how Mopidy is wired together with the MPD client,
the Spotify service, and the speakers.

**Legend**

- Filled red boxes are the key external systems.
- Gray boxes are external dependencies.
- Blue circles lives in the ``main`` process, also known as ``CoreProcess``.
  It is processing messages put on the core queue.
- Purple circles lives in a process named ``MpdProcess``, running an
  :mod:`asyncore` loop.
- Green circles lives in a process named ``GStreamerProcess``.
- Brown circle is a thread living in the ``CoreProcess``.

.. digraph:: class_instantiation_and_usage

    "main" [ color="blue" ]
    "CoreProcess" [ color="blue" ]

    # Frontend
    "MPD client" [ color="red", style="filled", shape="box" ]
    "MpdFrontend" [ color="blue" ]
    "MpdProcess" [ color="purple" ]
    "MpdServer" [ color="purple" ]
    "MpdSession" [ color="purple" ]
    "MpdDispatcher" [ color="blue" ]

    # Backend
    "Libspotify\nBackend" [ color="blue" ]
    "Libspotify\nSessionManager" [ color="brown" ]
    "pyspotify" [ color="gray", shape="box" ]
    "libspotify" [ color="gray", shape="box" ]
    "Spotify" [ color="red", style="filled", shape="box" ]

    # Output/mixer
    "GStreamer\nOutput" [ color="blue" ]
    "GStreamer\nSoftwareMixer" [ color="blue" ]
    "GStreamer\nProcess" [ color="green" ]
    "GStreamer" [ color="gray", shape="box" ]
    "Speakers" [ color="red", style="filled", shape="box" ]

    "main" -> "CoreProcess" [ label="create" ]

    # Frontend
    "CoreProcess" -> "MpdFrontend" [ label="create" ]
    "MpdFrontend" -> "MpdProcess" [ label="create" ]
    "MpdFrontend" -> "MpdDispatcher" [ label="create" ]
    "MpdProcess" -> "MpdServer" [ label="create" ]
    "MpdServer" -> "MpdSession" [ label="create one\nper client" ]
    "MpdSession" -> "MpdDispatcher" [
        label="pass requests\nvia core_queue" ]
    "MpdDispatcher" -> "MpdSession" [
        label="pass response\nvia reply_to pipe" ]
    "MpdDispatcher" -> "Libspotify\nBackend" [ label="use backend API" ]
    "MPD client" -> "MpdServer" [ label="connect" ]
    "MPD client" -> "MpdSession" [ label="request" ]
    "MpdSession" -> "MPD client" [ label="response" ]

    # Backend
    "CoreProcess" -> "Libspotify\nBackend" [ label="create" ]
    "Libspotify\nBackend" -> "Libspotify\nSessionManager" [
        label="creates and uses" ]
    "Libspotify\nSessionManager" -> "Libspotify\nBackend" [
        label="pass commands\nvia core_queue" ]
    "Libspotify\nSessionManager" -> "pyspotify" [ label="use Python\nwrapper" ]
    "pyspotify" -> "Libspotify\nSessionManager" [ label="use callbacks" ]
    "pyspotify" -> "libspotify" [ label="use C library" ]
    "libspotify" -> "Spotify" [ label="use service" ]
    "Libspotify\nSessionManager" -> "GStreamer\nProcess" [
        label="pass commands\nand audio data\nvia output_queue" ]

    # Output/mixer
    "Libspotify\nBackend" -> "GStreamer\nSoftwareMixer" [
        label="create and\nuse mixer API" ]
    "GStreamer\nSoftwareMixer" -> "GStreamer\nProcess" [
        label="pass commands\nvia output_queue" ]
    "CoreProcess" -> "GStreamer\nOutput" [ label="create" ]
    "GStreamer\nOutput" -> "GStreamer\nProcess" [ label="create" ]
    "GStreamer\nProcess" -> "GStreamer" [ label="use library" ]
    "GStreamer" -> "Speakers" [ label="play audio" ]


Thread/process communication
============================

.. warning::
    This section is currently outdated.

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
