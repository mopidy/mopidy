"""
Frontend which lets you control Mopidy through HTTP and WebSockets.

**Dependencies**

- ``cherrypy``

- ``ws4py``

**Settings**

- :attr:`mopidy.settings.HTTP_SERVER_HOSTNAME`

- :attr:`mopidy.settings.HTTP_SERVER_PORT`

- :attr:`mopidy.settings.HTTP_SERVER_STATIC_DIR`

**Usage**

When this frontend is included in :attr:`mopidy.settings.FRONTENDS`, it starts
a web server at the port specified by :attr:`mopidy.settings.HTTP_SERVER_PORT`.

As a simple security measure, the web server is by default only available from
localhost. To make it available from other computers, change
:attr:`mopidy.settings.HTTP_SERVER_HOSTNAME`. Before you do so, note that the
HTTP frontend does not feature any form of user authentication or
authorization. Anyone able to access the web server can use the full core API
of Mopidy. Thus, you probably only want to make the web server available from
your local network or place it behind a web proxy which takes care or user
authentication. You have been warned.

This web server exposes a WebSocket at ``/ws``. The WebSocket gives you access
to Mopidy's full API and enables Mopidy to instantly push events to the client,
as they happen.

The web server can also host any static files, for example the HTML, CSS,
JavaScript and images needed by a web based Mopidy client. To host static
files, change :attr:`mopidy.settings.HTTP_SERVER_STATIC_DIR` to point to the
directory you want to serve.

**API stability**

This frontend is currently to be regarded as **experimental**, and we are not
promising to keep any form of backwards compatibility between releases.
"""

# flake8: noqa
from .actor import HttpFrontend
