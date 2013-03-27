*********************
Extension development
*********************

.. warning:: Draft

    This document is a draft open for discussion. It shows how we imagine that
    development of Mopidy extensions should become in the future, not how to
    currently develop an extension for Mopidy.


Mopidy started as simply an MPD server that could play music from Spotify.
Early on Mopidy got multiple "frontends" to expose Mopidy to more than just MPD
clients: for example the Last.fm frontend what scrobbles what you've listened
to to your Last.fm account, the MPRIS frontend that integrates Mopidy into the
Ubuntu Sound Menu, and the HTTP server and JavaScript player API making web
based Mopidy clients possible. In Mopidy 0.9 we added support for multiple
music sources without stopping and reconfiguring Mopidy: for example the local
backend for playing music from your disk, the stream backend for playing
Internet radio streams, and the Spotify and SoundCloud backends, for playing
music directly from those services.

All of these are examples of what you can accomplish by creating a Mopidy
extension. If you want to create your own Mopidy extension for something that
does not exist yet, this guide to extension development will help you get your
extension running in no time, and make it feel the way users would expect your
extension to behave.


Anatomy of an extension
=======================

Extensions are all located in a Python package called ``mopidy_something``
where "something" is the name of the application, library or web service you
want to integrated with Mopidy. So for example if you plan to add support for a
service named Soundspot to Mopidy, you would name your extension's Python
package ``mopidy_soundspot``.

The name of the actual extension (the human readable name) however would be
something like "Mopidy-Soundspot". Make sure to include the name "Mopidy"
somewhere in that name and that you check the capitalization. This is the name
users will use when they install your extension from PyPI.

The extension must be shipped with a ``setup.py`` file and be registered on
`PyPI <https://pypi.python.org/>`_. Also make sure the development version link
in your package details work so that people can easily install the development
version into their virtualenv simply by running e.g. ``pip install
Mopidy-Soundspot==dev``.

Mopidy extensions must be licensed under an Apache 2.0 (like Mopidy itself),
BSD, MIT or more liberal license to be able to be enlisted in the Mopidy
Extension Registry. Keep in mind that the Mopidy Extension Registry is a
moderated place and libraries will be reviewed upfront if they behave as
required.


Notes
=====

An extension wants to:

- Be automatically found if installed
- Provide default config
- Validate configuration
- Validate presence of dependencies
  - Python packages (e.g. pyspotify)
  - Other software
  - Other extensions (e.g. SoundCloud depends on stream backend)
- Validate that needed TCP ports are free
- Be asked to start running
- Be asked to shut down
