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
not Mopidy.

.. digraph:: class_instantiation_and_usage

    "spytify" [ color="gray" ]
    "despotify" [ color="gray" ]
    "alsaaudio" [ color="gray" ]
    "__main__" -> "MpdServer" [ label="create 1" ]
    "__main__" -> "AlsaMixer" [ label="create 1" ]
    "__main__" -> "DespotifyBackend" [ label="create 1" ]
    "MpdServer" -> "MpdSession" [ label="create 1 per client" ]
    "MpdSession" -> "MpdHandler" [ label="pass MPD requests to" ]
    "MpdHandler" -> "DespotifyBackend" [ label="use backend API" ]
    "DespotifyBackend" -> "spytify" [ label="use Python wrapper" ]
    "spytify" -> "despotify" [ label="use C library" ]
    "DespotifyBackend" -> "AlsaMixer" [ label="use mixer API" ]
    "AlsaMixer" -> "alsaaudio" [ label="use Python library" ]
